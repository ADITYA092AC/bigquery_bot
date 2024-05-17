
import streamlit as st
from google.cloud import bigquery
import os
import pandas as pd
import google.generativeai as genai
import json

google_api_key = os.getenv("GOOGLE_API_KEY")
# os.environ["GOOGLE_API_KEY"] = "AIzaSyAVOqu6zxBPGCRRYMYrpyToLaDkhvW_nLU"

# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "credentials.json"


with st.sidebar:
    st.markdown("""<div style="display: block; font-size: 25px; font-weight: bold; padding-top: 5px; padding-bottom: 5px; padding-left: 0; padding-right: 0; border: 4px double #0077cc; color: #ff9900; text-align: center; border-radius: 10px; background-color: rgba(255, 255, 255, 0.5); box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);">BigQuery Bot</div>""", unsafe_allow_html=True)
    st.divider()
    json_file = st.file_uploader("Upload \n 'GOOGLE_APPLICATION_CREDENTIALS File' ", type='json')
    submit = st.button("Submit")
    
    if submit and json_file:
        # Save the uploaded file to disk
        with open("credentials.json", "wb") as f:
            f.write(json_file.read())
        with open('credentials.json') as f:
            project_name = json.load(f)['project_id']
       
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "credentials.json"
        st.success("Credentials uploaded successfully.")




def run_sql_query(qry):
    client = bigquery.Client()
    query_job = client.query(qry) 
    rows = query_job.result()
    r = rows.to_dataframe()
    return r


def prompt_maker():
    client = bigquery.Client()
    datasets = list(client.list_datasets())
    project = client.project
    main_text=''
    global tab_list
    tab_list=[]

    if datasets:
        for dataset in datasets:
            dataset_id=f"{project}.{dataset.dataset_id}"
            print(dataset_id)

            r=run_sql_query(f"""SELECT table_name, column_name,data_type,
            is_nullable FROM
            `{dataset_id}.INFORMATION_SCHEMA.COLUMNS`
            ;""")
            tables=list(set(r['table_name'].to_list()))
            count=0
         
            for i in tables:
                count+=1



                tab_list.append({"Alis Name":f"table{count}","Table":f"`{dataset_id}.{i}`"})

                schema=json.loads((r[r['table_name']==i][["column_name","data_type","is_nullable"]]).to_json())
                text=f"""
                    [table{count} name= `{dataset_id}.{i}` , table{count} SCHEMA = {schema}] and \n
                    """
                main_text+=text
    prompt="""Unlock your expertise in translating English queries into SQL commands! 
    You have a set of table names and their corresponding schemas in JSON format in a format of [table names,schemas] tailored for BigQuery SQL. 
    Your task is to craft precise SQL queries based on the questions I present, leveraging the given table schemas. 
    Remember, accuracy is key; ensure that your queries align with the table name,column names, column count, and data types specified for each table."""+main_text
    return prompt






prompt=prompt_maker()
def get_gemini_response(question):
    print(prompt)
    # st.sidebar.write(prompt)
    model=genai.GenerativeModel('gemini-pro')
    response=model.generate_content([prompt,question])
    return response.text.split("```")[1][3:]

ques=st.text_input("Ask your question")
try:
    prompt_maker()
    st.sidebar.dataframe(pd.DataFrame(tab_list),use_container_width=True,hide_index=True)
except:
    pass

if ques:
    with st.spinner("Just a sec! Brewing up a response for you! ☕️🐧" ):
        try: 
            response=get_gemini_response(ques)
            st.caption("SQL Query")
        except Exception as e:
            st.error(e)
        try:
            
            st.code(response,line_numbers=True,language="SQL")
            st.caption("Response")
            st.dataframe(run_sql_query(response),hide_index=True)
        except Exception as e:
            st.error(e)



