from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import configparser
import os
import sqlite3
import google.generativeai as genai



#configure gemini api key 
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

#function to load gemini model and generate SQL query as response
def get_gemini_res(prompt,question):
    model=genai.GenerativeModel('gemini-pro')
    response=model.generate_content([prompt[0],question])
    return response.text

#function to convert output into human readable format
def gen_gemini_finaloutput(prompt1,ques):
    model1=genai.GenerativeModel('gemini-pro')
    response1=model1.generate_content([prompt1[0],ques])
    return response1.text

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
  except:
    e="something is wrong with insertion"
    print(e)
    return e


#defining prompt:

prompt = [
    """
    you are an expert in converting english questions to SQL query!
    The SQL database has the name sqlite and has the following tables - CUSTOMERS, ORDER_ITEMS, SHIPMENTS, USER_INDEXES, USER_TABLES \n\n
    The table CUSTOMERS has the following columns - ORDER_ID, ORDER_TMS, CUSTOMER_ID, ORDER_STATUS, STORE_ID \n\n
    The table ORDER_ITEMS has the following columns - ORDER_ID, LINE_ITEM_ID, PRODUCT_ID, UNIT_PRICE, QUANTITY, SHIPMENT_ID \n\n
    The table SHIPMENTS has the following columns - SHIPMENT_ID, STORE_ID, CUSTOMER_ID, DELIVERY_ADDRESS, SHIPMENT_STATUS \n\n
    The table USER_TABLE has the following columns - DB_NAME, TABLE_NAME, COLUMN_NAME \n\n
    The table USER_INDEXES has the following columns - INDEX_ID, INDEX_NAME, TABLE_NAME, COLUMN_NAME \n\n
    The table STATS has the following columns - DB_NAME,TABLE_NAME, DB_SIZE, TABLE_SIZE\n\n
    Always enclose character data with single quotes\n\n
    use MIN,MAX,SUM,AVG for aggragate function in SQL queries\n\n
    use user_indexes for index related query and user_tables for column and table related information\n\n
    use like function to compare character values in where clause\n\n
    use rank funtion if requires partition, spliting, ranking or to check duplication\n\n
    Example 1 - How many entries of records are present in customers table?, the SQL command will be something like this \n''' SELECT COUNT(*) FROM CUSTOMERS;\n'''\n\n
    Example 2 - How many unique or distinct customer_id present in customers table?, the SQL command will be something like this \n''' SELECT count(distinct(customer_id)) FROM CUSTOMERS;\n'''\n\n
    Example 3 - which product has minimum quantity in order_items table?, the SQL command will be something like this \n''' SELECT product_id from order_items where quantity=(select min(quantity) from order_items);\n'''\n\n
    Example 4 - Insert the record (101,31-MAR-2023,300,complete,120) into customers table?, the SQL command will be something like this \n''' INSERT INTO CUSTOMERS(order_id,order_tms,customer_id,order_status,store_id) VALUES (101,'31-MAR-2023',300,'complete',120);\n'''\n\n
    Example 5 - Insert into customers table with values (101,31-MAR-2023,300,complete) ?, the SQL command will be something like this \n''' INSERT INTO CUSTOMERS(order_id,order_tms,customer_id,order_status,store_id) VALUES (101,'31-MAR-2023',300,'complete',NULL);\n'''\n\n  
    Example 6 - update the record in customers table with order_tms as  05-APR-24 where store_id as 107?, the SQL command will be something like this \n''' UPDATE CUSTOMERS SET ORDER_TMS='05-APR-24' WHERE STORE_ID = 107;\n'''\n\n
    Example 7 - Delete the record in customers table with store_id as 107?, the SQL command will be something like this \n''' DELETE FROM CUSTOMERS WHERE STORE_ID=107;\n'''\n\n
    Example 8 - Delete all the records in customers table?, the SQL command will be something like this \n''' DELETE FROM CUSTOMERS;\n'''\n\n
    Example 9- Fetch first 5 records in customers table with customer_id in descending order?, the SQL command will be something like this \n''' SELECT * from customers order by customer_id desc limit 5;\n'''\n\n
    Example 10 - How many x has been completed in y table?, the SQL command will be something like \n ''' SELECT COUNT(*) FROM Y WHERE x_status like "COMPLETE";\n'''\n\n
    Example 11 - How many indexes created on the customers table ? , the SQL command will be something like this \n''' SELECT count(column_name) from user_indexes WHERE table_name like 'customers';\n'''\n\n
    Example 12 - on which column index is created in customers table? , the SQL command will be something like this \n''' SELECT column_name FROM user_indexes WHERE UPPER(table_name) like 'customers';\n'''\n\n
    Example 13 - How many rows and columns present in the x table?, the SQL command will be something like this \n '''SELECT 'Row Count' AS type, COUNT(*) AS count FROM x UNION ALL SELECT 'Column Count' AS type, COUNT(*) AS count FROM pragma_table_info('x');\n'''\n\n
    Example 14 - How many tables present in sample schema/Database ? , the SQL command will be something like this \n''' SELECT distinct(table_name) from user_tables WHERE db_name like 'sample';\n'''\n\n
    Example 15 - fetch record with minimum quantity for the product id 21?, the SQL command will be something like this \n''' SELECT min(quantity),order_id from order_items o group by order_id having product_id =21;\n'''\n\n
    Example 16 - To get the row number based on order id by partition of line id from the table order items ?, the SQL command will be something like this \n''' SELECT product_id, order_id, row_number() over (partition by line_item_id order by order_id asc) from order_items;\n'''\n\n
    Example 17 - To fetch the shipment details from shipments table based on order_id ?, the SQL command will be something like this \n'''SELECT s.* FROM shipments s JOIN order_items o ON s.shipment_id = o.shipment_id;\n'''\n\n
    Example 18 - To get the total of sales amount whose shipment has been delivered?, the SQL command will be something like this \n'''SELECT SUM(o.quantity*o.unit_price) FROM shipments s JOIN order_items o ON s.shipment_id = o.shipment_id where s.shipment_status = "DELIVERED";\n'''\n\n
    Example 19 - what is the db_name for customers table_name in user_table ? , the SQL command will be something like this \n''' SELECT distinct(db_name) from user_tables WHERE table_name='customers';\n'''\n\n
    Example 20 - what is the database space left in the database?, the SQL command will be something like this \n''' SELECT DB_SIZE-(SUM(TABLE_SIZE)) FROM STATS \n'''\n\n
    Example 21 - what is the column_name for customers table_name in user_indexes table ? , the SQL command will be something like this \n''' SELECT column_name FROM user_indexes WHERE table_name='customers';\n'''\n\n
    Example 22 - what is the database space occupied by the tables?, the SQL command will be something like this \n''' SELECT SUM(TABLE_SIZE) FROM STATS \n'''\n\n
    Dont include ''' and \\n in the output
    """
]

prompt1 = [
    """
    you are an expert in converting the provided text to human readable format \n\n
    If there is any different query other than provided examples, simply return like this\n''' Below is the Result:\n'''\n\n
    Example 1 - How many records present in CUSTOMERS table?, the output will be something like this \n''' The total records in CUSTOMERS table is \n'''\n\n
    Example 2 - How many records present in CUSTOMERS and SHIPMENTS table?, the output will be something like this \n''' The total records in CUSTOMERS and SHIPMENTS table are\n'''\n\n
    Example 3 - what is the store id of cancelled order status in customers table? , the output will be something like this \n'''  The Store_id of cancelled order_status is \n'''\n\n
    Example 4 - How many columns are present in shipments table ? , the output will be something like this \n''' The total columns in shipments table is \n'''\n\n
    Example 5 - How many unique tables for customer id column name in user tables ? , the output will be something like this \n''' The total unique tables for customer id column name is \n'''\n\n
    Example 6 - what are the values present in user_tables ? , the output will be something like this \n''' The total values present in user_tables is \n'''\n\n
    Example 7 - How many entries for unit_price present in user_tables ? , the output will be something like this \n''' The total entries for unit_price in user_tables is \n'''\n\n 
    Example 8 - what is the db_name for customers table_name in user_table ? , the output will be something like this \n''' The db name for customers table is \n'''\n\n
    Example 9 - Give me index id for order id column name in user indexes table ? , the output will be something like this \n''' The index id for order id column name in user indexes table is \n'''\n\n
    Example 10 - what is the column name for customers in user indexes table ? , the output will be something like this \n''' The column name for customers in user indexes table is \n'''\n\n
    Example 11 - create plsql procedure to print quantity based on order id\n''' Below is the Procedure:\n'''\n\n
    Example 12 - create a plsql function to return  sum of unit price based on order id in order items table\n''' Below is the function:\n'''\n\n
    Example 13 - what is the sum of unit price from order items\n'''Below is the result:\n'''\n\n
    Dont include ''' and \\n in the output
    """
]

#Streamlit app for fetching data
# st.set_page_config(page_title="I can retrieve SQL query")
# st.header ("App for NL into SQL Data")
# question=st.text_input("Input to fetch Data: ",key="Input the Query")
# submit =st.button("Fetch Data")
# question1=st.text_input("Input for DML operation:",key="Enter the DML data")
# submit1= st.button("Update Data")
# if submit:
#     response = get_gemini_res(prompt,question)
#     print(response)
#     data=read_sql_query(response,"sqlite.db") 
#     print (data)
#     final_data=gen_gemini_finaloutput(prompt1,question)
#     print(final_data)
#     st.subheader(final_data)
#     for row in data:
#         x = list(row)
#         if len(x)==0:
#            st.header("no values retured")
#         elif len(x)<=1:
#          print(x[0])
#          st.header(x[0])
#         else:
#            st.header(x)

# if submit1:
#     res1 = get_gemini_res(prompt,question1)
#     print(res1)
#     DML_sql_query(res1,"sqlite.db")      
#     final_data=gen_gemini_finaloutput(prompt1,question1)
#     print(final_data)
#     st.subheader(final_data)

st.set_page_config(page_title="StreamSQL.AI", 
                   page_icon=":robot_face:",
                   layout="wide",
                   initial_sidebar_state="expanded"
                   )

def p_title(title):
    st.markdown(f'<h3 style="text-align: left; color:#F63366; font-size:28px;">{title}</h3>', unsafe_allow_html=True)

st.sidebar.header('StreamSQL.AI, I want to :crystal_ball:')
nav = st.sidebar.radio('',['Go to homepage', 'Fetch Data', 'Update Data'])


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

    # input_pa = st.text_area("Input your question here.", max_chars=500, height=100)

    question=st.text_area("Input to fetch Data: ",key="Input the Query", height=100)
    
    
    if st.button('Fetch') :
        if not question:
            st.warning('Oops, Input cant be empty')
        else:
            try :

              response = get_gemini_res(prompt,question)
              print(response)
              final_data=gen_gemini_finaloutput(prompt1,question)
              print(final_data)
              if all(element not in response for element in ["FUNCTION", "PROCEDURE", "TRIGGER"]):
                 data=read_sql_query(response,"sqlite.db") 
                 if not data :
                    st.warning('Sorry, i am not able to understand. Could you please rephrase it ?')
                 else:
                    st.subheader(final_data)
                    for row in data:
                     x = list(row)
                     if len(x) == 1:
                        print(x[0])
                        st.header(x[0])
                     else:
                         st.subheader(x)   
              else:
                  st.subheader(response)          
              

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

    question1=st.text_area("Input for DML operation:",key="Enter the DML data", height=100)

    if st.button('Update') :
             res1 = get_gemini_res(prompt,question1)
             print(res1)
             result=DML_sql_query(res1,"sqlite.db")      
             st.subheader(result)

 