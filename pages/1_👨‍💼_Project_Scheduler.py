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
QUERY_TEMPLATE2="""
select a.quotation_No,a.room_type,a.service, b.duration from `final_dataset.project_schedule` as a
        inner join `final_dataset.quotation_duration` as b
        ON a.quotation_No = b.quotation and a.room_type = b.room
        group by a.quotation_No,a.room_type,a.service,b.duration
"""

query2 = QUERY_TEMPLATE2.format(limit=1000)
query_job2 = bq_client.query(query2)
rows2 = query_job2.result()
df2 = rows2.to_dataframe()

QUERY_TEMPLATE = """ Select quotation_id as id,service_types from final_dataset.quotation_values
        """
query = QUERY_TEMPLATE.format(limit=1000)
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



my_index_endpoint = aiplatform.MatchingEngineIndexEndpoint("98203980546441216")
DEPLOYED_INDEX_ID = "project_schedule_final_03020808"

generation_model = TextGenerationModel.from_pretrained("text-bison@001")
models = GenerativeModel("gemini-pro")

Assistant = st.chat_message("Assistant")
Assistant.write("Hello! I'm your friendly AI assistant from Asian Paints Beautiful Homes Service. I'm here to help you keep your home renovation project on track and sparkling, just like your future new space!  Let me know how I can assist with your project schedule.")

prompt = st.chat_input("How can i assist you ?")
ques = prompt
if prompt:
    users = st.chat_message("user")
    users.write(ques)
    with st.spinner('Genrating an output...'):
        Context = """You are project schedule manager and you have to generate project schedule for house.
         If the given question is not related to creating a project schedule, Please decline the question in sarcastic or witty way depending on question. 
        
        Greet users if they greet you.
        Do not respond to one word question.
        
        If general question is asked like Create project schedule or project schedule, respond by asking for which room types he wants to create a project schedule.
        
        Strictly return Proceed if the user asked specifically like creating a project schedule for home or creating project schedule for different rooms inside house .  
        If the question is related to project schedule for home decor but room types or service is not mentioned, ask user for the room types for what they want the projct schedule. 


         """


        question= {prompt}
        prompts = f"""Answer the question given the context below as {{Context:}}. \n
            Context: {Context}?\n
            Question: {question} \n
            Answer:
            """
        
        output = generation_model.predict(prompts,max_output_tokens=1024).text

        if output != "Proceed":
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
            num_neighbors=5,
            )
            
            arr=[]
            id_arr=[]

            for idx, neighbor in enumerate(response[0]):
                id = np.str_(neighbor.id)
                similar = df.query("id == @id", engine="python")
                id_arr.append(id)
                
            for id in id_arr:
                similar = df2.query('quotation_No == "%s"' %id, engine="python")
                for i in range(0,len(similar)):
                    arr.append(similar.values[i])
                    
            
            
            context = """
                You are a Project Scheduling Manager and you have to provide a schedule of completing renovation or service of renovations of home decor.
                You will be given the certain sets of [quation number, Room Type, Work Type, Duration] in the same format.
                
                 Create a detailed scheduled with time durations in step by step manner with tentative duration for different task based on room type , work type and duration.
            
                Only create project schedule for room types mentioned in the {{question2}}. 
                If work type is mentioned in {{question2}} generate for that work types only. If work type is not mentioned generate for all the work-type for that room type you can find in {{reference}}.
                
                Work Type Sequence is : Demolition then Civil then Electrical then Painting then Furniture then Miscallaenous

                Determine the sequence of work type from above and generate accordingly.
                
                Take Average Duration for each Work type matching room type from {{Reference}} where Duration is the last value in {{reference}} and give description of what needs to be done for each service step by step manner.
                                
                Do not display the {{prompt}}.
                
                                
      
  
                """
            
            question= f"{ques} based on {{Context}} below."
            prompt = f"""
                Context: {context}?\n
                Question: {question}
                Question2: {ques} \n
                Reference :{arr}
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
            
           