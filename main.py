import requests
import openai
import glob
import os
import keys
from langs import langs
from notion.client import NotionClient
from notion.block import CodeBlock
from notion.block import PageBlock
from notion.block import TextBlock
from notion.block import CalloutBlock

code_path = '/Users/chaseungjun/Desktop/Code/Python/Baekjoon'
openai.api_key = keys.openai
notion_token_v2 = keys.token
notion_page_id = keys.page_id
def code_comments(param):
    try:
        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=[
                {'role': 'system', 'content': ''},
                {'role': 'user', 'content': "다음 코드의 작동 원리를 간결하게 한글로 설명해라 (말투는  \"~이다\"): " + param}
            ],
            temperature=0.4
        )
    except:
        print("OpenAI API Error!")
        return
    return response['choices'][0]['message']['content']

def get_problem(prob_n):
    url = "https://solved.ac/api/v3/problem/show"
    querystring = {"problemId": str(prob_n)}
    headers = {"Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers, params=querystring)
    except:
        print("Solved.ac API ERROR!")
        return
    return response.json()

def extract_prob_info(data):
    problemId = data['problemId']
    titleKo = data['titleKo']
    level = data['level']
    tags = [tag['displayNames'][0]['name'] for tag in data['tags']]
    return [problemId, titleKo, level, tags]

def save_file_list(path):
    file_list = []
    for root, dirs, files in os.walk(path):
        for file_name in files:
            file_list.append(root + '/' + file_name)
    return file_list

def post_page(problem_info, submit_code, client):
    page = client.get_block(notion_page_id)

    # page title
    post_title = str(problem_info[0]) + ' - ' + problem_info[1]
    new_page = page.children.add_new(PageBlock, title=post_title)

    # problem link
    link_text_block = new_page.children.add_new(TextBlock)
    link_text_block.title = f'[문제 링크](https://www.acmicpc.net/problem/{problem_info[0]})'

    # page icon
    tier = str(problem_info[2])
    icon_url = f'https://d2gd6pc034wcta.cloudfront.net/tier/{tier}.svg'
    new_page.icon = icon_url

    # page callout
    callout_info = '/'.join(problem_info[3])
    callout = new_page.children.add_new(CalloutBlock)
    callout.title = callout_info
    callout.icon = "💡"
    callout.color = "gray_background"

    # read code
    submit_path = glob.glob(f'{code_path}/{problem_info[0]}.*')[0]
    with open(submit_path, "r", encoding='utf-8') as f:
        code_lines = f.readlines()
    code_lines = ['    ' + line for line in code_lines]
    code = ''.join(code_lines)

    # code block
    new_code_block = new_page.children.add_new(CodeBlock)
    new_code_block.title = code
    new_code_block.language = submit_code

    # code comments
    new_text_block = new_page.children.add_new(TextBlock)
    new_text_block.title = code_comments("\n".join(code_lines))

def update_notion(f_list):
    try:
        client = NotionClient(token_v2=notion_token_v2)
    except:
        print("Notion Client Error!")
        return
    page = client.get_block(notion_page_id)

    # get list of current pages in page
    current_pages = []
    for child in page.children:
        if isinstance(child, PageBlock):
            cut = child.title.index(' ')
            current_pages.append(child.title[:cut])

    for f_name in f_list:
        f_name = f_name[::-1]
        dot = f_name.index('.')
        slash = f_name.index('/')

        # get problem id
        problem_id = f_name[dot + 1:slash][::-1]
        if problem_id in current_pages:
            continue

        # get submit code
        code_file = f_name[:dot + 1][::-1]
        submit_code = langs[code_file]

        problem_info = extract_prob_info(get_problem(problem_id))
        post_page(problem_info, submit_code, client)

f_list = save_file_list(code_path)
update_notion(f_list)