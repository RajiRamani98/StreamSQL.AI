from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import os
import sqlite3
import google.genai as genai
from google.genai import types
from prompts import SYSTEM_SQL_PROMPT, SYSTEM_OUTPUT_PROMPT

# Load .env from the app directory explicitly
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_client():
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        api_key = api_key.strip().strip('"').strip("'")
    if not api_key:
        raise RuntimeError("Missing Google Generative AI API key. Set GOOGLE_API_KEY or GEMINI_API_KEY in .env")
    return genai.Client(api_key=api_key)


try:
    client = get_client()
except Exception as exc:
    client = None
    CLIENT_INIT_ERROR = exc
else:
    CLIENT_INIT_ERROR = None

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
FALLBACK_MODEL_NAME = "gemini-2.0-flash"


def infer_target_table(question):
    normalized = (question or "").lower()

    shipment_terms = [
        "shipment", "shipments", "delivery", "deliver", "dispatch",
        "tracking", "track", "shipment_status", "shipment id", "shipment_id",
        "shipping"
    ]
    item_terms = [
        "line item", "line_item", "line-item", "item", "items",
        "product", "products", "quantity", "unit price", "price", "sku"
    ]
    order_terms = ["order", "customer", "customer_id", "order_status", "store", "order_tms"]
    metadata_size_terms = ["db size", "table size", "database size", "storage", "size", "db_size", "table_size"]
    metadata_index_terms = ["index", "indexes", "indexed", "indexes created", "index metadata"]
    metadata_table_terms = ["table metadata", "table schema", "table structure", "columns", "column", "metadata", "schema"]

    if any(term in normalized for term in metadata_size_terms):
        return "STATS"
    if any(term in normalized for term in metadata_index_terms):
        return "USER_INDEXES"
    if any(term in normalized for term in metadata_table_terms):
        return "USER_TABLES"
    if any(term in normalized for term in shipment_terms):
        return "SHIPMENTS"
    if any(term in normalized for term in item_terms):
        return "ORDER_ITEMS"
    if any(term in normalized for term in order_terms):
        return "CUSTOMERS"
    return None


def build_sql_prompt(question):
    target_table = infer_target_table(question)
    if not target_table:
        return question

    if target_table == "SHIPMENTS":
        return (
            f"IMPORTANT: This request is about shipment information. "
            f"Use SHIPMENTS as the primary table. Do not use ORDER_ITEMS for shipment, delivery, or tracking questions.\n"
            f"User request: {question}"
        )

    if target_table == "ORDER_ITEMS":
        return (
            f"IMPORTANT: This request is about item-level details. "
            f"Use ORDER_ITEMS as the primary table.\n"
            f"User request: {question}"
        )

    return (
        f"IMPORTANT: This request is about order/customer information. "
        f"Use CUSTOMERS as the primary table.\n"
        f"User request: {question}"
    )


def extract_sql_from_text(text):
    import re

    if not text:
        return ""

    text = text.strip()
    fence_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", text, re.S | re.I)
    if fence_match:
        text = fence_match.group(1).strip()

    text = text.replace("`", "").strip()
    statement_match = re.search(r"\b(select|insert|update|delete|with)\b[\s\S]*", text, re.I)
    if statement_match:
        statement = statement_match.group(0).strip()
        semicolon_match = re.search(r"(.*?;)\s*", statement, re.S)
        if semicolon_match:
            return semicolon_match.group(1).strip()
        return statement

    return text


# function to load gemini model and generate SQL query as response
def get_gemini_res(question):
    client_instance = get_client()
    enhanced_question = build_sql_prompt(question)

    for model_name in [MODEL_NAME, FALLBACK_MODEL_NAME]:
        try:
            response = client_instance.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_text(text=SYSTEM_SQL_PROMPT),
                    types.Part.from_text(text=enhanced_question),
                ],
                config=types.GenerateContentConfig(
                    max_output_tokens=512,
                    temperature=0.15,
                ),
            )
            return extract_sql_from_text(response.text)
        except Exception as exc:
            if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc) or "quota" in str(exc).lower():
                continue
            raise

    raise RuntimeError("The AI service is currently unavailable due to quota limits. Please try again shortly.")

#function to convert output into human readable format
def gen_gemini_finaloutput(question):
    client_instance = get_client()

    for model_name in [MODEL_NAME, FALLBACK_MODEL_NAME]:
        try:
            response = client_instance.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_text(text=SYSTEM_OUTPUT_PROMPT),
                    types.Part.from_text(text=question),
                ],
                config=types.GenerateContentConfig(
                    max_output_tokens=256,
                    temperature=0.15,
                ),
            )
            return response.text.strip()
        except Exception as exc:
            if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc) or "quota" in str(exc).lower():
                continue
            raise

    raise RuntimeError("The AI service is currently unavailable due to quota limits. Please try again shortly.")


def is_sql_query(text):
    if not text:
        return False
    normalized = text.strip().lower()
    return normalized.startswith(("select", "insert", "update", "delete", "with"))


def is_dml_query(text):
    if not text:
        return False
    normalized = text.strip().lower()
    return normalized.startswith(("insert", "update", "delete"))


def clean_summary_text(text):
    import re

    if not text:
        return ""

    text = text.replace("\r\n", "\n")
    text = re.sub(r'```(?:sql)?\s*.*?\s*```', '', text, flags=re.S | re.I)
    text = re.sub(r'###\s*', '', text)
    text = re.sub(r'\[([^\]]*)\]\(([^)]+)\)', r'\1', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'`([^`]*)`', r'\1', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

#Db connection for fetching Data
def read_sql_query(sql,db):
    conn=sqlite3.connect(db)
    cur=conn.cursor()
    cur.execute(sql)
    rows=cur.fetchall()
    conn.commit()
    conn.close()
    for row in rows:
      print(row)
    return rows

# Db connection for DML operation
def DML_sql_query(que,db):
  try:
    con=sqlite3.connect(db)   
    cur=con.cursor()
    cur.executescript(que)
    con.commit()
    con.close()
    return "Operation success"
  except Exception as e:
    print(e)
    return "Something is wrong with the insertion or update statement."

st.set_page_config(page_title="StreamSQL.AI", 
                   page_icon="🤖",
                   layout="wide",
                   initial_sidebar_state="expanded"
                   )

def p_title(title):
    st.markdown(f'<h3 style="text-align: left; color:#F63366; font-size:28px;">{title}</h3>', unsafe_allow_html=True)

st.sidebar.header('StreamSQL.AI, I want to :crystal_ball:')
nav = st.sidebar.radio('Choose a page', ['Go to homepage', 'Fetch Data', 'Update Data'], label_visibility='collapsed')


if nav == 'Go to homepage':

    st.markdown("<h1 style='text-align: center; color: white; font-size:28px;'>Welcome to StreamSQL.AI!</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; font-size:56px;'<p>&#129302;</p></h3>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: grey; font-size:20px;'>Streams SQL Queries using NLP in this Data-Driven World of Ours!</h3>", unsafe_allow_html=True)
    
    st.markdown('___')
    st.write(':point_left: Use the menu at left to select a task (click on > if closed).')
    st.markdown('___')
    st.markdown("<h3 style='text-align: left; color:#F63366; font-size:18px;'><b>What is this App about?<b></h3>", unsafe_allow_html=True)
    st.write("Learning happens best when content is personalized to meet our needs and strengths.")
    st.write("For this reason I created StreamSQL.AI :robot_face:, the AI system to accelerate and design your knowledge in seconds! Use this App to interact with the database system and retrieve the accurate results.You can fetch and update data From/To database without writing the actual query language. Write or Paste your text and you're done. We'll process it for you!")     
    st.markdown("<h3 style='text-align: left; color:#F63366; font-size:18px;'><b>Who is this App for?<b></h3>", unsafe_allow_html=True)
    st.write("Anyone can use this App, regardless of their SQL knowledge, to effortlessly execute SQL queries using intuitive and human-readable natural language inputs. ")

if nav == 'Fetch Data' :

    st.markdown("<h4 style='text-align: center; color:grey;'>Accelerate knowledge with StreamSQL.AI &#129302;</h4>", unsafe_allow_html=True)
    st.text('')
    p_title('Fetch Data')
    st.text('')

    question = st.text_area("Input to fetch Data:", key="Input the Query", height=100)

    if st.button('Fetch') :
        if not question:
            st.warning('Oops, Input cant be empty')
        else:
            try:
                generated_sql = get_gemini_res(question)
                st.markdown('**Generated SQL:**')
                st.code(generated_sql, language='sql')

                if not is_sql_query(generated_sql):
                    st.error('AI did not generate a valid SQL statement. Please rephrase your request.')
                else:
                    data = read_sql_query(generated_sql, "sqlite.db")
                    if not data:
                        st.warning('Sorry, I am not able to understand. Could you please rephrase it?')
                    else:
                        row_count = len(data)
                        st.subheader(f'Query results ({row_count} rows)')
                        st.table(data)
            except Exception as e:
                st.error(f'An error occurred: {e}')
                print(e)
    else :
        st.info('Please submit your query to get a response.')

if nav == 'Update Data' :

    st.markdown("<h4 style='text-align: center; color:grey;'>Accelerate knowledge with StreamSQL.AI &#129302;</h4>", unsafe_allow_html=True)
    st.text('')
    p_title('Update data')
    st.text('')

    question1 = st.text_area("Input for DML operation:", key="Enter the DML data", height=100)

    if st.button('Update') :
        if not question1:
            st.warning('Input cannot be empty')
        else:
            try:
                generated_sql = get_gemini_res(question1)
                st.markdown('**Generated SQL:**')
                st.code(generated_sql, language='sql')

                if not is_dml_query(generated_sql):
                    st.error('AI did not generate a valid INSERT/UPDATE/DELETE statement. Please rephrase your request.')
                else:
                    result = DML_sql_query(generated_sql, "sqlite.db")
                    st.subheader(result)
            except Exception as e:
                st.error(f'An error occurred: {e}')
                print(e)

 