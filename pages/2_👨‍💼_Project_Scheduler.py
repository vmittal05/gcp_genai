import streamlit as st
import plotly.express as px
import time
from datetime import datetime
import sys
import pandas as pd
from google.cloud import aiplatform
from google.cloud import bigquery
import vertexai
from vertexai.preview.language_models import TextEmbeddingModel
import numpy as np
from vertexai.language_models import TextGenerationModel
import random
from vertexai.generative_models import GenerativeModel
import subprocess


st.set_page_config(
    page_title="Project Scheduler" ,
    page_icon="👨‍💼",
)

PROJECT_ID = "dark-caldron-414803"  
LOCATION = "us-central1"
my_index_endpoint = aiplatform.MatchingEngineIndexEndpoint("885911702871212032")
DEPLOYED_INDEX_ID = "embvs_tutorial_deployed_02261247"


aiplatform.init(project=PROJECT_ID, location=LOCATION)
vertexai.init(project=PROJECT_ID, location=LOCATION)

bq_client = bigquery.Client(project=PROJECT_ID)
QUERY_TEMPLATE = """
        select a.*, b.duration from `DummyDataset.Site_Detail` as a
        left outer join `DummyDataset.Duraion_Detail` as b
        ON a.quotation_No = b.quotation
        AND a.Room_Type = b.room;
        """
query = QUERY_TEMPLATE.format()
query_job = bq_client.query(query)
rows = query_job.result()
df = rows.to_dataframe()

model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")

BATCH_SIZE=5
def get_embeddings_wrapper(texts):
    embs = []
    for i in (range(0, len(texts), BATCH_SIZE)):
        time.sleep(1)  # to avoid the quota error
        result = model.get_embeddings(texts[i : i + BATCH_SIZE])
        embs = embs + [e.values for e in result]
    return embs



my_index_endpoint = aiplatform.MatchingEngineIndexEndpoint("885911702871212032")
DEPLOYED_INDEX_ID = "embvs_tutorial_deployed_02261247"

generation_model = TextGenerationModel.from_pretrained("text-bison@001")
models = GenerativeModel("gemini-pro")

Assistant = st.chat_message("Assistant")
Assistant.write("Hey ! How can i assist you ?")

prompt = st.chat_input("Enter your Room Type")
ques = prompt
if prompt:
    users = st.chat_message("user")
    users.write(ques)
    with st.spinner('Genrating an output...'):
        Context = """You are project schedule manager or Event Plan generator. Your task is to create a project schedule for house.
         If the given question is not related to home decor or project schedule, Please decline the question in sarcastic or witty way depending on question. 
        
         Strictly return true if it is related home decor, Home, room types inside home or project schedule .   

        If you cannot figure out context, decline the question. 

        Do not return false as an anwser in any situation.
         """


        question= {prompt}
        prompts = f"""Answer the question given the context below as {{Context:}}. \n
            Context: {Context}?\n
            Question: {question} \n
            Answer:
            """
        
        output = generation_model.predict(prompts,max_output_tokens=1024).text

        if output != "True":
            def stream_data():
                for word in output.split():
                    yield word + " "
                    time.sleep(0.02)


            with st.chat_message("Assistant"):
                st.write_stream(stream_data)
            
        else:        

            test_embeddings = get_embeddings_wrapper([prompt])

            response = my_index_endpoint.find_neighbors(
            deployed_index_id=DEPLOYED_INDEX_ID,
            queries=test_embeddings,
            num_neighbors=1,
            )
            arr=[]
            i=0
            # show the result


            for idx, neighbor in enumerate(response[0]):
                id = np.int64(neighbor.id)
                arr.append([])
                similar = df.query("id == @id", engine="python")
                arr[i].append(similar.Location.values[0])
                arr[i].append(similar.Tier.values[0])
                arr[i].append(similar.Room_Type.values[0])
                arr[i].append(similar.Service.values[0])
                arr[i].append(similar.duration.values[0])
                i=i+1
                #st.write(arr[i-1])
            

            context = """
                You are a Project Scheduling Manager and you have to provide a schedule of completing renovation or service of renovations of home decor.
                Create a detailed scheduled with time durations in step by step manner.

                Only write the task related to {similar.Service.values[0]} service for renovated home.
                
                If any extra detail is mentioned in Question2 use that also to form an response.

                Do not display the {{prompt}}.
                
                Output strictly should look like below example format only. Do not add ''' quptes.:
                
                    Project Schedule for Washroom Renovation

                    Service Type: Furniture Work (15 days)

                    Day 1-3: Demolition and Removal

                    Remove existing furniture, fixtures, and cabinetry.
                    Prepare the space for new furniture installation.
                    Day 4-6: Installation of New Furniture

                    Install new vanity, mirror, and storage cabinets.
                    Mount towel racks and other accessories.
                    Day 7-9: Painting and Refinishing

                    Paint or refinish walls, trim, and cabinetry.
                    Install new flooring (if necessary).
                    Day 10-12: Electrical and Plumbing

                    Install new lighting fixtures and electrical outlets.
                    Connect plumbing fixtures and appliances.
                    Day 13-15: Final Touches

                    Install shower curtain and accessories.
                    Add decorative elements (e.g., artwork, plants).
                    Clean and inspect the finished space.



        
  
                """
            
            question= f"Create a detailed project Schedule for renovation/new house of {similar.Room_Type.values[0]} which will do {similar.Service.values[0]} work and is scheduled for {similar.duration.values[0]}  days"
            prompt = f"""
                Context: {context}?\n
                Question: {question}
                Question2: {ques} \n
                """
        


            output = models.generate_content(prompt).text

            AI =  st.chat_message("Assistant")              
            AI.markdown(f"{output}")

            gantt_chart = models.generate_content(""" generate a data frame for below Project Schedule based in duration for each tasks, "
                                                  Data frame should look like this : pd.DataFrame([
                                                                                    dict(Task="Job A", Start='2009-01-01', Finish='2009-02-28'),
                                                                                    dict(Task="Job B", Start='2009-03-05', Finish='2009-04-15'),
                                                                                    dict(Task="Job C", Start='2009-02-20', Finish='2009-05-30')
                                                 Only give output as pd.dataframe... Do not include import statements. Do not assign data frame to varibale. Just return as mentioned format.
                                                 Take Job A start date as mentioned in question in format 'YYYY-MM-DD'. 
                                                 If start Date is not given in query, use '2024-03-04'.
])"""                           + output).text
            new_gantt_chart = gantt_chart.replace("```","")
            new_gantt_chart = new_gantt_chart.replace("python","")
            df = pd.DataFrame()
            
            df = eval(new_gantt_chart)

            fig = px.timeline(
                    df,
                    x_start="Start", 
                    x_end="Finish", 
                    y="Task"
                )
            fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up
            
            st.plotly_chart(fig, theme="streamlit")
            
           