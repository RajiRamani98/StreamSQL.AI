from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import os
import sqlite3
import google.genai as genai
from google.genai import types

# Load .env from the app directory explicitly
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# Configure Gemini API key
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if api_key:
    api_key = api_key.strip().strip('"').strip("'")
if not api_key:
    raise RuntimeError("Missing Google Generative AI API key. Set GOOGLE_API_KEY or GEMINI_API_KEY in .env")

# Use Google GenAI client with API key
client = genai.Client(api_key=api_key)
MODEL_NAME = "gemini-flash-latest"

SYSTEM_SQL_PROMPT = """
You are a SQL generation assistant. Use the SQLite schema below to generate exactly one valid SQL statement.
The database has these tables and columns:
CUSTOMERS(ORDER_ID, ORDER_TMS, CUSTOMER_ID, ORDER_STATUS, STORE_ID)
ORDER_ITEMS(ORDER_ID, LINE_ITEM_ID, PRODUCT_ID, UNIT_PRICE, QUANTITY, SHIPMENT_ID)
SHIPMENTS(SHIPMENT_ID, STORE_ID, CUSTOMER_ID, DELIVERY_ADDRESS, SHIPMENT_STATUS)
USER_TABLES(DB_NAME, TABLE_NAME, COLUMN_NAME)
USER_INDEXES(INDEX_ID, INDEX_NAME, TABLE_NAME, COLUMN_NAME)
STATS(DB_NAME, TABLE_NAME, DB_SIZE, TABLE_SIZE)

Rules:
- Output only a single valid SQL statement.
- Do not add explanation, markdown, comments, or code fences.
- Use single quotes for string values.
- Use SELECT for read queries.
- Use INSERT, UPDATE, DELETE for write queries.
- Use the exact values from the user's request; do not invent or replace numbers.
- When the user says "update <table> from <old> to <new>", translate that to an UPDATE with the same primary key column set to <new> and a WHERE clause matching <old>.
- For SHIPMENTS, if the request is to update shipment id values, generate `UPDATE SHIPMENTS SET SHIPMENT_ID = <new> WHERE SHIPMENT_ID = <old>`.
- If the user asks for orders or order data, prefer CUSTOMERS.
- If the user asks for shipment details, prefer SHIPMENTS.
- If the user asks for item-level details, prefer ORDER_ITEMS.
- If unsure, return the best fitting query using the schema.
"""

SYSTEM_OUTPUT_PROMPT = """
You are an expert assistant that converts SQL results into a short, human-readable summary.
Return only the summary without extra formatting.
"""


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
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Part.from_text(text=SYSTEM_SQL_PROMPT),
            types.Part.from_text(text=question),
        ],
        config=types.GenerateContentConfig(
            max_output_tokens=512,
            temperature=0.15,
        ),
    )
    return extract_sql_from_text(response.text)

#function to convert output into human readable format
def gen_gemini_finaloutput(question):
    response = client.models.generate_content(
        model=MODEL_NAME,
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

    text = re.sub(r'```(?:sql)?\s*.*?\s*```', '', text, flags=re.S | re.I)
    text = re.sub(r'###\s*', '', text)
    text = re.sub(r'\[([^\]]*)\]\(([^)]+)\)', r'\1', text)
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

 