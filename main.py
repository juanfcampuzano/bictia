from fastapi import FastAPI
import requests
import json
import re
from youtubesearchpython import VideosSearch

app = FastAPI()


@app.get("/{role}")
def post_ruta_educativa(role: str):
    
    role = role.replace('_', ' ')
    headers = {"Content-Type": "application/json", 'Authorization': 'Bearer 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'}

    url = "https://api.openai.com/v1/chat/completions"

    prompt = f"""Imagina que eres un experto en curriculum designer. Dame un curriculum para aprender a ser """+role+""" con los temarios, ordenados por secciones y por subsecciones, agregando el tiempo aproximado de estudio para cada uno. Quiero la respuesta en formato json {'seccion1':{'subseccion1':{'tema1':'tiempo1}}} no acepto mas formatos, si no me mandas el formato json mi app crashea"""

    data = {

        "model": "gpt-3.5-turbo",
        "max_tokens": 3500,
        "messages":[
                {"role": "system", "content": "You are a chatbot"},
                {"role": "user", "content": prompt},
            ]
    }

    response = requests.post(url, headers=headers, json=data)

    response_dict = json.loads(response.text)

    print(response_dict)


    respuesta_chatgpt = response_dict['choices'][0]['message']['content']
    respuesta_chatgpt = re.sub(r'\n\s*', '', respuesta_chatgpt)

    regex = r'^[^{]*({[\s\S]*})[^}]*$'

    print(respuesta_chatgpt)

    try:
        json_str = re.findall(regex, respuesta_chatgpt)[0]
    except:
        respuesta_chatgpt = respuesta_chatgpt+'}'
        json_str = re.findall(regex, respuesta_chatgpt)[0]

    loaded_json = json.loads(json_str)

    ruta_educativa = []

    for seccion in loaded_json.keys():
        seccion_actual = loaded_json[seccion]
        for subseccion in seccion_actual.keys():
            subseccion_actual = seccion_actual[subseccion]
            if type(subseccion_actual) == str:
                row = {}
                videosSearch = VideosSearch(subseccion, limit = 1)
                result = videosSearch.result()['result'][0]
                row['seccion'] = [seccion]
                row['tema'] = [subseccion]
                row['titulo_video'] = [result['title']]
                row['url_video'] = [result['link']]
            else:
                for tema in subseccion_actual.keys():
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