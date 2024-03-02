import streamlit as st
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

Assistant = st.chat_message("Assistant")
Assistant.write("Hey ! How can i assist you ?")

prompt = st.chat_input("Enter your Room Type")
ques = prompt
if prompt:
    users = st.chat_message("user")
    users.write(ques)
    with st.spinner('Genrating an output...'):
        Context = """You are project schedule manager or Event Plan generator. Your task is to create a project schedule for house.
         If the given question is not related to home decor or project schedule, Please decline the question in humorous,sarcastic way depending on questions context 
        
         Strictly return true if it is related home decor, Home, room types inside home or project schedule .   

        If you cannot figure out context, decline the question, do not return false.
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
                You are a Project Scheduling Manager and you have to provide a schedule of completing the provided details.
                Room Type can be of Kids Room , Entertainment Room , Washroom , Terrace , Pooja Room,
                Kitchen , Lawn , Porch, Study room , Bedroom, Looby/Passage , Other Room.
 
                The input text will be in sequece of [ location1, Tier1, Room Type1, Service Type1 and duration1 ],[ location2, Tier2, Room Type2, Service Type2 and duration2 ].
                Subtask will be of type Installation, Delivery, Painting, Ceiling, Putty etc
 
                Create an output as a project schedule with Task, Subtask and Duration.
 
                Different service type tasks are as below,  create subtasks from taking the below reference:
                If furniture is service type then subtask will be- Furniture installation, Furniture Assemble, Furniture Cleaning
                IF Furnishing is service type then subtask will be- Polishing,
                If Wooden Ceiling is service type then subtask will be- Importing, Implementing
                If Electrical is service type then subtask will be- Wiring, Fixing Issues, Testing
                If Paints is service type then subtask will be- Old paint Scrapping, Putty, New Paintinh
                If Miscellaneous is service type then subtask will be- Railing, Water Proofing, Final Cleaning
                If Civil is service type then subtask will be- Demolition , Installation, Plaster, Mounting
 
                Addition of Subtasks duration should be equal to Total Duration.
                Below is the sample of how output schould be displayed.
                Create atleast 2 proposals with at least 2 subtasks.
               
 
                Input : ["29.0588° N, 76.0856° E","Tier III","Kitchen","Furniture","55" ],["19.9975° N, 73.7898° E","Tier II","Kitchen","Civil","23" ]
                output :
 
                ''' '
                Here's you project schedule for {Room Type} for {Service1} & {Service2}
 
    Proposal 1:
                Type: Furniture           Total Duration : 55
 
                SubTask: Furniture installation              
                SubTask: Furniture Assemble                  
                SubTask: Furniture Cleaning                    
 
    Proposal 2:
                Type: Civil               Total Duration : 23
 
                SubTask: Demolition          
                SubTask: Installation        
                SubTask: Mounting    

                """
            
            z = random.randint(0, 4)
            question= f"Create a project Schedule for workers for renovation of {similar.Room_Type.values[0]} which will do {similar.Service.values[0]} work and is scheduled for {similar.duration.values[0]}  days"
            prompt = f"""Answer the question given the context below as {{Context:}}. \n
                Context: {context}?\n
                Question: {question} \n
                Answer:
                """
        


            output = generation_model.predict(prompt).text

            AI =  st.chat_message("Assistant")              
            AI.markdown(f"{output}")

            