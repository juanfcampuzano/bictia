from fastapi import FastAPI
import requests
import json
from fastapi.middleware.cors import CORSMiddleware
import re
from youtubesearchpython import VideosSearch
from bardapi import Bard
import pickle as pkl
import os
import boto3
from fastapi_scheduler import SchedulerAdmin
from fastapi_amis_admin.admin.site import AdminSite
from fastapi_amis_admin.admin.settings import Settings

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

site = AdminSite(settings=Settings(database_url_async='sqlite+aiosqlite:///amisadmin.db'))
scheduler = SchedulerAdmin.bind(site)

def save_to_local(obj, name):
    pkl.dump(obj, open('pkl-data/'+str(name)+'.pkl', 'wb'))

def save_to_s3(obj, name):
    print('SUBIENDO {} a s3'.format(name))
    os.environ['AWS_ACCESS_KEY_ID'] = 'AKIAT36HIHLLWYBJ4VK6'
    os.environ['AWS_SECRET_ACCESS_KEY'] = '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'
    s3 = boto3.client('s3')
    bucket = 'profile-matching-coally'  # Reemplaza con el nombre de tu bucket en S3
    key = str(name)+'.pkl'  # Reemplaza con la ruta y nombre de archivo en S3
    s3.put_object(Body=pkl.dumps(obj), Bucket=bucket, Key=key)
    print('SUBIDO {} a s3'.format(name))

def download_from_s3(name, path):
    print('DESCARGANDO '+name +' DE S3')
    s3 = boto3.client('s3',
                  aws_access_key_id='AKIAT36HIHLLWYBJ4VK6',
                  aws_secret_access_key='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')

    # Descarga el archivo PKL de S3 y guárdalo localmente
    nombre_archivo_local = str(path)+str(name)+'.pkl'
    s3.download_file('profile-matching-coally', str(name)+'.pkl', nombre_archivo_local)
    print('TERMINE DE DESCARGAR '+name +' DE S3')


@app.post("/save_chatgpt_query")
def save_chatgpt_query(id_user, role, answer):
    tries = 0

    while tries < 5:
        try:
            chatgpt_responses = pkl.load(open('pkl-data/chatgpt_responses.pkl', 'rb'))
            temp_dict = {}
            temp_dict['role']=role
            temp_dict['response']=answer
            chatgpt_responses[id_user] = temp_dict
            save_to_local(chatgpt_responses, 'chatgpt_responses')
            save_to_s3(chatgpt_responses, 'chatgpt_responses')
        except:
            continue

    chatgpt_responses = {}
    temp_dict = {}
    temp_dict['role']=role
    temp_dict['response']=answer
    chatgpt_responses[id_user] = temp_dict
    save_to_local(chatgpt_responses, 'chatgpt_responses')
    save_to_s3(chatgpt_responses, 'chatgpt_responses')


@app.get("/{role}")
def post_ruta_educativa(role: str):
    
    role = role.replace('_', ' ')

    token = 'WwjjqNqGPs1ijNEKQHSEyLjwQDxgCEzLXhd113fhV5jWpHU0V9L0NTpQo8WP2dSbiHWamQ.'
    query = '''imagine you are a curriculum designer. Please design for me a curriculum for being a '''+role+'''. Provide it in a json format like this example {
    "Core Curriculum": {
        "Introduction to Data Analysis": ["What is data analysis?", "The data analysis process", "Data types and structures"],
        "Data Wrangling": ["Data cleaning", "Data transformation", "Data integration"],
        "Statistical Analysis": ["Descriptive statistics", "Inferential statistics", "Regression analysis"],
        "Machine Learning": ["Supervised learning", "Unsupervised learning", "Deep learning"],
        "Data Visualization": ["Creating data visualizations", "Interpreting data visualizations"]
    },
    "Technical Skills": {
        "Programming": ["Python", "SQL"],
        "Data Science Tools": ["R", "Tableau", "Power BI"],
        "Cloud Computing": ["AWS", "Azure", "Google Cloud Platform"]
    },
    "Soft Skills": {
        "Communication": ["Presenting data", "Writing reports"],
        "Problem Solving": ["Identifying problems", "Developing solutions"],
        "Critical Thinking": ["Analyzing data", "Making decisions"],
        "Teamwork": ["Working with others", "Collaborating on projects"]
    }
    }'''

    bard = Bard(token=token)
    bard.get_answer(query)['content']

    string = bard.get_answer(query)['content']
    first_curly = string.find('{')
    last_curly = string.rfind('}')
    string = string[first_curly:last_curly+1]

    loaded_json = json.loads(re.sub(' +', ' ', string.replace('\n','')).replace(', }','}').replace(',}','}'))

    ruta_educativa = []

    for seccion in loaded_json.keys():
        seccion_actual = loaded_json[seccion]

        if type(seccion_actual) == dict:
            subsecciones = seccion_actual.keys()
        elif type(seccion_actual) == list:
            subsecciones = seccion_actual
        else:
            subsecciones = seccion_actual.keys()

        for subseccion in subsecciones:
            if type(seccion_actual) == dict:
                subseccion_actual = seccion_actual[subseccion]
            else:
                subseccion_actual = subseccion
            if type(subseccion_actual) == str:
                row = {}
                videosSearch = VideosSearch(subseccion, limit = 1)
                result = videosSearch.result()['result'][0]
                row['seccion'] = [seccion]
                row['tema'] = [subseccion]
                row['titulo_video'] = [result['title']]
                row['url_video'] = [result['link']]
            else:
                for tema in subseccion_actual:
                    row = {}
                    videosSearch = VideosSearch(tema, limit = 1)
                    result = videosSearch.result()['result'][0]
                    row['seccion'] = [seccion]
                    row['subseccion'] = [subseccion]
                    row['tema'] = [tema]
                    row['titulo_video'] = [result['title']]
                    row['url_video'] = [result['link']]

            ruta_educativa.append(row)
    return ruta_educativa

@app.on_event("startup")
async def startup():
    site.mount_app(app)
    download_from_s3('chatgpt_responses','')
    scheduler.start()