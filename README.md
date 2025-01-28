## 1. Introduction

We present a Web Based Application using Python, Streamlit, and Gen AI allowing you to make natural language queries to your database.

StreamSQL.AI is a LLM application using Google Gemini where we will create Text To SQL via LLM App and later retrieving query results from database in the form of NLP.

This application is a Python project that seamlessly blends the power of Natural Language Processing (NLP) with SQL database queries. This interactive application allows users, regardless of their SQL knowledge, to effortlessly execute SQL queries using intuitive and human-readable natural language inputs.

It’s a demo application where we prompt engineer the LLM models for our database to perform SQL queries and also, create PL/SQL scripts.

## 2. Model Usage

The application is highly valuable as it enables individuals without SQL knowledge to effortlessly query the database using natural language. 

In this specific use case, consider a scenario where we have customer data, any non-it professional can use plain English to query for customer to retrieve results. This intuitive approach empowers v various teams to make data-driven decisions and target high-probability customer segments effectively. With real-time insights at their fingertips, teams can focus on converting potential leads with ease and efficiency.

## 3. Tech Stack
The project leverages the following technologies:

Python: The primary programming language used for developing the application.
Streamlit: A user-friendly web framework for creating interactive data apps, serving as the user interface.
Google Gemini Pro: The advanced NLP language model used for transforming natural language prompts into SQL queries. Google Gemini is a family of multimodal large language models developed by Google DeepMind, serving as the successor to LaMDA and PaLM 2. Comprising Gemini Ultra, Gemini Pro, Gemini Flash, and Gemini Nano
SQLite3: It is a database engine written in the C programming language. It is not a standalone app; rather, it is a library that software developers embed in their apps. As such, it belongs to the family of embedded databases.

## 4. Sample Database and LLM Training

We have used SQLite3 as backend Database engine. We created a sample database called “sqlite.db”. It has end user data tables such as Customers, Order_items, Shipments and metadata tables such as Stats, User_indexes, User_tables. 
We created the sample prompts for training the LLM model to generate SQL queries appropriately.
Firstly, we have to emphasize the LLM about the task it is going to perform. Prompt example: you are an expert in converting english questions to SQL query!
Secondly, we have to provide database details and its table details to LLM with the below mentioned prompt data:
The SQL database has the name sqlite and has the following tables - CUSTOMERS, ORDER_ITEMS, SHIPMENTS, USER_INDEXES, USER_TABLES \n\n
    The table CUSTOMERS has the following columns - ORDER_ID, ORDER_TMS, CUSTOMER_ID, ORDER_STATUS, STORE_ID \n\n
    The table ORDER_ITEMS has the following columns - ORDER_ID, LINE_ITEM_ID, PRODUCT_ID, UNIT_PRICE, QUANTITY, SHIPMENT_ID \n\n
    The table SHIPMENTS has the following columns - SHIPMENT_ID, STORE_ID, CUSTOMER_ID, DELIVERY_ADDRESS, SHIPMENT_STATUS \n\n
    The table USER_TABLE has the following columns - DB_NAME, TABLE_NAME, COLUMN_NAME \n\n
    The table USER_INDEXES has the following columns - INDEX_ID, INDEX_NAME, TABLE_NAME, COLUMN_NAME \n\n
    The table STATS has the following columns - DB_NAME,TABLE_NAME, DB_SIZE, TABLE_SIZE\n\n
Atlast, we have to provide the sample queries using the provided sample table data.
Example: How many unique or distinct customer_id present in customers table?, the SQL command will be something like this \n''' SELECT count(distinct(customer_id)) FROM CUSTOMERS;\n'''\n\n

## 5. Evaluation Results

METADATA SCENARIO:

Short Description: To fetch the table metadata information stored in the Database.

Brief Description: The query is to fetch the number of rows and columns in the CUSTOMERS table is provided into the text prompt of UI. The Gen AI creates the SQL for the provided query and execution done using Python SQLite3 Package.

Input to fetch data:
To fetch number of rows and columns in customers table

Below is the Result:
The total records in CUSTOMERS table is The total columns in CUSTOMERS table is

['Row Count', 5]
['Column Count', 5]

## 6. How to Run Locally

DeepSeek-V3 can be deployed locally using the following open-source community software:

1. **Streamlit**: To design lightweight web application, streamlit needs to be installed.
2. **GenerativeAI**: To generate queries based on provided prompts, we need Google LLM model Generative AI.
### To generate Google API key:
    
    Go to [Click Google AI Studio](https://aistudio.google.com/).
    Log in with your Google account.
    Create an API key and store it in .env file and import the file into your Python IDE.
   
2. **dotenv**: Python dotenv is a powerful tool that makes it easy to handle environment variables in Python applications from start to finish.

Below are the commands used for installation of Streamlit, GenerativeAI and dotenv:
```shell
pip install -r requirements.txt
```


#### System Requirements

> [!NOTE] 
> Mac and Windows are supported with Python IDE.

