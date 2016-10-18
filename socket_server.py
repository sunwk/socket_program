import socket
import time
import urllib.parse
import json

# 首页视图函数
def index():
    html = b'HTTP/1.x 200 OK\r\nContent-Type: text/html\r\n\r\n<h1>Hello World</h1><img src="doge.gif"/>'
    return html


# /doge.gif 下的视图函数
def image():
    with open('doge.gif', 'rb') as f:
        header = b'HTTP/1.x 200 OK\r\nContent-Type: image/gif\r\n\r\n'
        img = header + f.read()
        return img


# /time 路径下的视图函数
def time_response(query):
    html = 'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<h1>Time: {}</h1><hr>{}'.format(time.time(), query)
    return html.encode('utf-8')

# 这是/message对应的视图函数
def save(msgs):
    with open('db.db', 'a+') as f:
        f.write(json.dumps(msgs))

# 载入已提交数据的函数
def load():
    try:
        with open('db.db', 'r') as f:
            return json.loads(f.read())
    except:
        return []

# 读取html模板
def template_from(name):
    with open(name, 'r', encoding='utf-8') as f:
        return f.read()

# 拼装 响应行 + header + body
def response_with(body='', response_header=None, http_header=None):
    h = 'HTTP /1.1 200 OK'
    header_dict = {
        'Content-Type': 'text/html'
    }
    header = '\r\n'.join(['{}: {}'.
                         format(k, v) for k, v in header_dict.items()])
    response = h + '\r\n' + header + '\r\n\r\n' + body
    return response


messages = load()
# body默认为空，在GET方法时不会有body传入，POST时才会有，此时它们已经被解析为字典
def message(query, body={}):
    print("msg query", query)
    print("body, update, ", body)

    # 无论是get还是post传的参都用query装起来，类似于flask的query
    query.update(body)

    m = query.get('neirong', '')
    m = urllib.parse.unquote(m)
    if len(m) > 0:
        messages.append(m)
        save(messages)

    # 这是一个html分割线的标签，让每一条留言之间能够分开
    msg = '<hr>'.join(messages)
    form = template_from('message.html')
    html = response_with(form.format(msg,))
    return html.encode('utf-8')

# 解析参数，返回字典
def parsed_arguments(s):
    d = {}
    if len(s) < 1:
        return d
    items = s.split('&')
    # ['neirong=nihao']
    print('items, ', items, len(items))
    for i in items:
        k, v = i.split('=')
        d[k] = v
    return d

def response_for_path(path, body):
    query = {}
    # 解析 body 中的 GET 传过来的参数
    if '?' in path:
        path, query = path.split('?')
        query = parsed_arguments(query)
    # 解析 body 中的 POST 传过来的参数
    form = parsed_arguments(body)
    r = {
        '/': index(),
        '/doge.gif': image(),
        '/time': time_response(query),
        '/message': message(query, form),
    }
    page404 = b'HTTP/1.x 404 NOT FOUNT\r\n\r\n<h1>NOT FOUND</h1>'
    return r.get(path, page404)


host = ''
port = 3004
# 初始化socket
s = socket.socket()
#绑定主机名和端口
s.bind((host, port))
while True:
    # 监听发往指定主机名和端口的连接请求
    s.listen(7)
    # 接受发来的请求，得到套接字，与客户端建立连接
    connection, address = s.accept()
    print('connection, address debug',connection, address)
    # 接受request
    request = connection.recv(1024)
    request = request.decode('utf-8')
    print("debug request, ", request,'debug request finished')
    # 判断客户端是否发送空请求，如果是直接关掉这个连接，避免阻塞
    if len(request) == 0:
        connection.close()
        continue
    #  GET /message?neirong=nihao HTTP/1.1\r\n   split把request分开，取出包含参数的path
    path = request.split()[1]
    print('ip and request, {}\n{}'.format(address, request))


    body = ''
    r = request.split('\r\n\r\n', 1)
    print('debug, r', len(r), r[1])
    if len(r) > 1:
        body = r[1]
    print('body ', body)
      response = response_for_path(path, body)
    print('response, ', path, response)
    '''
    bug记录：这里本来写的是print('response, ', path, response.decode('utf-8'))   本意为打印出response，但是这里会出出现一个问题，即需要发送doge.gif时
    response里边是包含了这个动图的，这个动图在在index()视图函数里是在html标签里链接过来的，会被整个response前的b''转化为二进制
    在image()视图函数里也是是以rb二进制读格式打开的。且与b''形式的header拼接在一起了，这里再试图decode会将图片也一起decode()成字符串，
    这显然是不可以的，所以会出错：
    UnicodeDecodeError: 'utf-8' codec can't decode byte 0xf6 in position 54: invalid start byte
    然后还会有一些其他严重后果：
     （1）当path = '/'时，只会导致index()视图函数的<img src="doge.gif"/>'标签里链接挂掉，显示结果是'hello world'正常显示，动图会裂掉
     （2）当path = '/doge.gif'时，则会导致链接直接挂掉，代码模拟的服务器程序直接终止。
    '''
    connection.sendall(response)

    connection.close()
