from fastapi import FastAPI
import requests
import json
from fastapi.middleware.cors import CORSMiddleware
import re
from youtubesearchpython import VideosSearch
from bardapi import Bard

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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