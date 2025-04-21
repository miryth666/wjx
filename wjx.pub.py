# 时间：2025/4/1022:46
'''弄好了过后搬过来的，这个例子告诉我们，还是要把普通的东西(请求头)先排除了再去想高级反爬'''
import os
import pprint
import traceback
from bs4 import BeautifulSoup
import ddddocr
ocr = ddddocr.DdddOcr()
import requests
import re
import time
import random
from colorama import init, Fore
init(True)
def generate_unique_path(file_path,sep='()'):
    if len(sep) not in (0,1,2):
        raise ValueError('不支持连接符长于2')
    left_sep = right_sep = ''
    if len(sep)==2:
        left_sep = sep[0]
        right_sep = sep[1]
    elif len(sep)==1:
        left_sep = sep
    # 如果路径不存在，直接返回
    if not os.path.exists(file_path):
        return file_path
    # 分离路径的文件名和扩展名
    directory, filename = os.path.split(file_path)
    name, ext = os.path.splitext(filename)
    # 初始化序号
    counter = 1

    # 生成新路径，直到找到一个不重复的路径
    while True:
        new_filename = f"{name}{left_sep}{counter}{right_sep}{ext}"
        new_path = os.path.join(directory, new_filename)
        if not os.path.exists(new_path):
            return new_path
        counter += 1
def submit(shortid,requests_result,data):
    res = requests_result
    rndnum = re.findall(r'var rndnum="(.*?)";',res.text)
    jqnonce = re.findall(r'var jqnonce="(.*?)";',res.text)
    starttime = re.findall(r'<input type="hidden" value="(.*?)" id="starttime" name="starttime"',res.text)
    try:
        if not len(rndnum)==len(jqnonce)==len(starttime)==1: # 第一次尝试这种写法，本来想尝试all的
            print(f'正则表达式获取数量不匹配，分别：{len(rndnum)}:{len(jqnonce)}:{len(starttime)}')
        rndnum, jqnonce, starttime = rndnum[0],jqnonce[0],starttime[0]
        cook = res.cookies
        # input(str(cook))
        # time.sleep(2) # 确定性时延
    except:
        traceback.print_exc()
        print('程序继续执行！')
    # 固定参数
    def dataenc(e, ktimes):
        t = ktimes % 10
        if t == 0:
            t = 1
        result = []
        for char in e:
            n = ord(char) ^ t
            result.append(chr(n))
        return ''.join(result)
    submittype = '1'
    nw = '1'
    jwt = '8' # 跟问卷有关
    jpm = '36'# 跟问卷有关
    wxfs = '100'
    ktimes = 408 + random.randint(1,56)  # 示例值，可动态调整

    current_time = int(time.time() * 1000)
    cst = str(current_time)
    t = str(current_time + random.randint(232, 620))  # 与 cst 时间戳接近
    jqsign = dataenc(jqnonce, ktimes)

    # 构建参数字典
    params = {
        "starttime": starttime,  # 后面经过血的教训发现这个参数不可缺！否则显示答卷时间为0秒
        "shortid": shortid,
        "ktimes": str(ktimes),
        "jqnonce": jqnonce,
        "jqsign": jqsign
    }
    # print(params)
    h = {'host': 'www.wjx.cn', 'origin': 'https://www.wjx.cn', 'referer': f'https://www.wjx.cn/vm/{shortid}.aspx',
         'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"', 'sec-ch-ua-mobile': '?0',
         'sec-ch-ua-platform': '"Windows"', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors',
         'sec-fetch-site': 'same-origin',
         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
         'x-requested-with': 'XMLHttpRequest'}

    response = requests.post(
        url="https://www.wjx.cn/joinnew/processjq.ashx",  # 替换为实际URL
        params=params,cookies = cook,data = data,headers=h
    )
    if response.status_code == 200 and 'wjx/join' in response.text:
        print(Fore.GREEN+'成功！'*5)
    elif response.text=='22' or '问卷地址错误' in response:
        print(Fore.RED+'失败！'*5)
    else:
        print('疑似失败！')
    # print("请求状态码:", response.status_code)
    # print("响应内容:", response.text)

# 题型映射字典
QUESTION_TYPES = {
    '1': '填空题',
    '2': '多行填空题',
    '3': '单选题',
    '4': '多选题'
}


def parse_questions(html_content):
    """
    解析 HTML 内容，提取题目信息并按顺序返回。
    返回格式：包含所有题目信息的字典列表。
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    try:
        title = soup.select('#htitle')[0].text
        print(Fore.RED+f'问卷标题：{title.strip()}')
    except:
        pass
    questions = soup.find_all('div', class_='field')

    parsed_questions = []

    for question in questions:
        # 提取题号
        topic_number = question.get('topic', 'xxx')

        # 提取 type 属性
        question_type_code = question.get('type', 'xxx')
        question_type = QUESTION_TYPES.get(question_type_code, '未知题型')

        # 提取题目标题
        title_div = question.find('div', class_='topichtml')
        title = title_div.get_text(strip=True) if title_div else "无标题"

        # 提取图片链接（如果有）
        img_link = ""
        img_tag = title_div.find('img') if title_div else None
        if img_tag:
            img_link = img_tag.get('src', 'xxx')

        # 提取选项、提示和其他信息，根据题型不同处理逻辑
        options = []
        rows = []
        columns = []
        min_value = ""
        max_value = ""
        is_required = question.get('req') == '1'
        tip_text = ""

        # 根据题型提取特定信息
        if question_type_code == '3' or question_type_code == '4':  # 单选题或多选题
            radio_options = question.find_all('div', class_='ui-radio')
            checkbox_options = question.find_all('div', class_='ui-checkbox')
            if radio_options or checkbox_options:
                for option in radio_options + checkbox_options:
                    label = option.find('div', class_='label')
                    if label:
                        options.append(label.get_text(strip=True))
            tip_span = question.find('span', class_='qtypetip')
            if tip_span:
                tip_text = tip_span.get_text(strip=True)

        elif question_type_code == '6' or question_type_code == '9':  # 矩阵题
            matrix_table = question.find('table', class_='matrix-rating')
            if matrix_table:
                # 提取行标题
                row_titles = matrix_table.find_all('tr', class_='rowtitle')
                for row in row_titles:
                    title_span = row.find('span', class_='itemTitleSpan')
                    if title_span:
                        rows.append(title_span.get_text(strip=True))

                # 提取列标题
                column_headers = matrix_table.find('tr', class_='trlabel')
                if column_headers:
                    columns = [th.get_text(strip=True) for th in column_headers.find_all('th') if
                               th.get_text(strip=True)]

        elif question_type_code == '8':  # 滑动条题
            min_input = question.find('input', {'min': True})
            max_input = question.find('input', {'max': True})
            if min_input:
                min_value = min_input.get('min', 'xxx')
            if max_input:
                max_value = max_input.get('max', 'xxx')

        elif question_type_code == '11':  # 排序题
            options_list = question.find_all('li', class_='ui-li-static')
            if options_list:
                for option in options_list:
                    span = option.find('span')
                    if span:
                        options.append(span.get_text(strip=True))

        # 构建题目信息字典
        question_info = {
            "题号": topic_number,
            "题型": question_type,
            "标题": title,
            "图片链接": img_link,
            "选项": options,
            "行标题": rows,
            "列标题": columns,
            "最小值": min_value,
            "最大值": max_value,
            "提示": tip_text,
            "必填": is_required,
            "备注": None # 这个是自己写程序需要传递的，如图片识别内容
        }

        parsed_questions.append(question_info)

    return parsed_questions

def get_pic(pic_url):
    if pic_url.startswith('//'):
        pic_url = 'https:' + pic_url
    res = requests.get(pic_url,headers={'referer':'https://www.wjx.cn/'})
    if res.status_code == 403:
        print('[获取图片端]: 失败')
    else:
        if 'jpg' in pic_url:
            path = generate_unique_path('data/demo.jpg')
            with open(path,'wb') as f:
                f.write(res.content)
                # os.startfile(os.path.abspath(path))
            return path
        elif 'png' in pic_url:
            path = generate_unique_path('data/demo.png')
            with open(path,'wb') as f:
                f.write(res.content)
                # os.startfile(os.path.abspath(path))
            return path
        else:
            print('[图片抓取函数]：图片无后缀名！')
            return None
def rec_pic(pic_path):
    # 读取验证码图片
    if os.path.exists(pic_path):
        with open(pic_path, 'rb') as f:
            img_bytes = f.read()
        # 识别验证码
        result = ocr.classification(img_bytes)
        if result:
            print('[识图端]:',result)
            return result
        else:
            print('[识图端]: 识图未成功！！已经执行打开图片')
            os.startfile(os.path.abspath(pic_path))
    else:
        print('[识图端]: 图片文件不存在！')
def print_questions(url):
    html_content = requests.get(url)
    questions = parse_questions(html_content)
    # 打印结果
    for idx, question in enumerate(questions, 1):
        print(f"\n=== 题目 {idx} ===")
        print(f"题号: {question['题号']}")
        print(f"题型: {question['题型']}")
        print(f"标题: {question['标题']}")

        if question['图片链接']:
            url = question['图片链接'] if question['图片链接'].startswith('http') else 'https:'+question['图片链接']
            print(f"图片链接: {url}")

        if question['选项']:
            print("选项:", ", ".join(question['选项']))

        if question['行标题']:
            print("行标题:", ", ".join(question['行标题']))

        if question['列标题']:
            print("列标题:", ", ".join(question['列标题']))

        if question['提示']:
            print(f"提示: {question['提示']}")

        if question['最小值'] or question['最大值']:
            print(f"范围: {question['最小值']} - {question['最大值']}")

        print(f"必填: {'是' if question['必填'] else '否'}")
        print("-" * 50)
def handle_questions(questions_data):
    if all([i.get('题型') in ['填空题','多行填空题','单选题','多选题'] for i in questions_data]):
        print(Fore.GREEN+f'一共{len(questions_data)}个题目，且全部为简单类型题目')
        pics = [i.get('图片链接') for i in questions_data]
        if any(pics):
            print(f'含有{len([True for i in pics if i])}项图片题')
            print('正在识图处理')
            res_lst = []
            for i in questions_data:
                if i.get('图片链接'):
                    path = get_pic(i.get('图片链接'))
                    text = rec_pic(path)
                    if text:
                        if not i.get('标题'):
                            i['标题'] = text
                        else:
                            i['备注'] = text
                        print(f'第{i.get("题号")}题：识图结果：{text}！')
                        res_lst.append(True)
                    else:
                        print(Fore.RED+f'第{i.get("题号")}题：识图未成功！')
                        res_lst.append(False)
            print(Fore.GREEN+f'[问题处理端]: 图片识别完毕({res_lst.count(True)}项成功，{res_lst.count(False)}项失败)，结果如下：\n',questions_data)
        print('[问题处理端]: 正在进行答案匹配！')
        '''目前设计的是，如果又有标题又有图片(备注)，那么需要精确匹配，否则接入AI，如果只有标题，则可以精确或模糊'''
        final_lst = []
        for i in questions_data:
            if i.get('备注'):
                res = match_question(i.get('备注'))
                if res and res[1]:
                    ans = res[0]
                    print(f'[问题匹配端]: 第{i.get("题号")}题已精确匹配到答案({ans})！')
                    
                else:
                    # AI接入处理 【dg】：可以修改！目前人工
                    options = [str(i.get('选项').index(_)+1)+'.'+_ for _ in i.get('选项')]
                    question = f'请你直接给出这个问题的正确选项序号：{i.get("标题")}：{i.get("备注")}  选项：{"  ".join(options)}' if options else f'请你直接给出这个问题的答案：{i.get("标题")}：{i.get("备注")}' # 注意这一行是用的选项来判断是不是选择题，如果增加了题目类型就不严格！
                    ans = manu_answer(question)
            elif i.get('标题'):
                res = match_question(i.get('标题'))
                if res:
                    ans = res[0]
                    if res[1]:
                        print(f'[问题匹配端]: 第{i.get("题号")}题已精确匹配到答案！({ans})')
                    else:
                        print(Fore.YELLOW+f'[回答端]: 第{i.get("题号")}题已粗略匹配到答案！(题目：{i.get("标题")},匹配答案：{ans})')
                else:
                    # AI接入处理 【dg】：可以修改！目前人工
                    options = [str(i.get('选项').index(_) + 1) + '.' + _ for _ in i.get('选项')]
                    question = f'请你直接给出这个问题的正确选项序号：{i.get("标题")}  选项：{"  ".join(options)}' if options else f'请你直接给出这个问题的答案：{i.get("标题")}'  # 注意这一行是用的选项来判断是不是选择题，如果增加了题目类型就不严格！
                    ans = manu_answer(question)
            else:
                print(Fore.RED+f'[问题匹配端]: 第{i.get("题号")}题：暂不支持无标题的题目！默认-3')
                ans = '-3'
            # 这么下来都有ans了
            answer = match_answer(i,ans)
            if not answer:
                # 【dg】：可以修改！修改方向：图片可以直接展示图片窗格，也可以接入AI
                options = [str(i.get('选项').index(_) + 1) + '.' + _ for _ in i.get('选项')]
                question = f'请你直接给出这个问题的正确选项序号：{i.get("标题")}  选项：{"  ".join(options)}' if options else f'请你直接给出这个问题的答案：{i.get("标题")}'  # 注意这一行是用的选项来判断是不是选择题，如果增加了题目类型就不严格！
                answer = manu_answer(question)
            else:
                print(f'[答案匹配端]: 第{i.get("题号")}题已正确处理！')
            # 现在一定有answer了
            final_lst.append('$'.join([i.get('题号'),answer]))
        else:
            final_str = '}'.join(final_lst)
            print(Fore.GREEN+'[问题处理端]: 发送数据已生成！如下\n',final_str)
            final_data = {'submitdata':final_str}
            # submit()
            return final_data
    else:
        print(Fore.RED+'含有复杂题型（暂不支持处理）!!!')
        input()
def match_question(question:str):
    '''设想的是几个规则：1.完全匹配 2.包含匹配'''
    global matches
    if question in matches:
        v = matches.pop(question) # 这个是为了防止多个题对照到同一个键
        return (v,True)
    else:
        for i in matches:
            if i in question:
                v = matches.pop(i)  # 这个是为了防止多个题对照到同一个键
                return (v, False)
        return None
def match_answer(question:dict,answer):
    '''判断题型，进行作答，如果是选择题，则从answer中匹配答案'''
    if question.get('题型') in ['填空题','多行填空题']:
        return answer
    elif question.get('题型') == '单选题':
        options: list = question.get('选项')
        if answer in options:
            return str(options.index(answer)+1)
        for i in options:
            if answer in i:
                return str(options.index(i)+1)
        return None
    else:
        print(Fore.RED+f'[答案匹配端]: 不支持该类题型({question.get("题型")})')
def manu_answer(question):
    '''人工回答问题'''
    # print(Fore.RED + 'AI接入处理（暂未做）')
    print(Fore.RED + '=' * 20)
    print(Fore.RED + '【进行人工作答】')
    print(Fore.RED + '=' * 20)
    ans = input(question + '回答输入后enter')
    return ans
if __name__ == '__main__':
    # 常见问题匹配：
    matches = {
        '姓名': 'xxx',
        '班级': 'xxx',
        '院系': 'xxx',
        '学院': 'xxx',
        '学校': 'xxx',
        '年级': 'xxx',
        '小班': 'xxx',
        '大班': 'xxx',
        'QQ': 'xxx',
        'qq': 'xxx',
        'Qq': 'xxx',
        'qQ': 'xxx',
        '电话': 'xxx',
        'phone':'xxx',
        '学号': 'xxx',
        '性别': 'xxx',
        '微信': 'xxx',
        '邮箱': 'xxx',
        '预留': 'xxx',
    }
    url = input('问卷网址')
    pattern = r"https://www\.wjx.*/vm/([A-Za-z0-9]+)\.aspx"
    if len(url)!=7:
        id = re.search(pattern,url).group(1)
    # print(id)
    js = 0
    html = requests.get(url,headers={'accept': 'application/json, text/plain, */*', 'accept-encoding': 'gzip, deflate, br, zstd', 'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8', 'cache-control': 'no-cache', 'connection': 'keep-alive', 'content-length': '0', 'pragma': 'no-cache', 'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-site', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'})
    # 这里要做一个忙等待
    while '很抱歉' in html.text or '距离开始' in html.text:
        js +=1
        html = requests.get(url,headers={'accept': 'application/json, text/plain, */*', 'accept-encoding': 'gzip, deflate, br, zstd', 'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8', 'cache-control': 'no-cache', 'connection': 'keep-alive', 'content-length': '0', 'pragma': 'no-cache', 'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-site', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'})
        print(Fore.YELLOW+f'等待中！(等待第{js}次)',end=' ')
        time.sleep(0.7)
    st = time.time()
    data = parse_questions(html.text)
    # print(data)
    send_data = handle_questions(data)
    print(Fore.RED+f'已经耗时：{time.time()-st:.3}秒！') # 在刚写完识图的时候，这个全部操作不用多线程也就1.18秒
    print('即将启动发送程序！！')
    submit(id,html,send_data)
