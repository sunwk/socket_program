import socket
import ssl


def parsed_url(url):
    # 检查协议
    protocol = 'http'
    if url[:7] == 'http://':
        u = url.split('://')[1]
    elif url[:8] == 'https://':
        protocol = 'https'
        u = url.split('://')[1]
    else:
        # '://' 定位 然后取第一个 / 的位置来切片
        u = url

        # 检查默认 path
    i = u.find('/')
    if i == -1:
        host = u
        path = '/'
    else:
        host = u[:i]
        path = u[i:]

        # 检查端口
    port_dict = {
        'http': 80,
        'https': 443,
    }
    port = port_dict[protocol]
    if host.find(':') != -1:
        h = host.split(':')
        host = h[0]
        port = int(h[1])

        # print(protocol, host, path, port)
    return protocol, host, port, path


def socket_by_protocol(protocol):
    if protocol == 'http':
        s = socket.socket()
    else:
        s = ssl.wrap_socket(socket.socket())
    return s


def response_by_socket(s):
    response = b''
    buffer_size = 1024
    while True:
        r = s.recv(buffer_size)
        response += r
        if len(r) == 0:
            break
    return response


def parsed_response(r):
    header, body = r.split('\r\n\r\n', 1)
    h = header.split('\r\n')
    status_code = h[0].split()[1]
    status_code = int(status_code)

    headers = {}
    for line in h[1:]:
        k, v = line.split(': ')
        headers[k] = v
    return status_code, headers, body


def get(url):
    # 解析输入url
    protocol, host, port, path = parsed_url(url)
    # 根据protocol是http还是https来判断连接方式是否加密，继而判断是用socket.socket()还是ssl.wrap_socket(socket.socket()) 。ps：用https 的 socket 连接需要 import ssl 并且使用 s = ssl.wrap_socket(socket.socket()) 来初始化
    s = socket_by_protocol(protocol)
    # 通过host和port来向服务器发出连接请求
    s.connect((host, port))
    # 拼接request
    request = 'GET {} HTTP/1.1\r\nhost:{}\r\n\r\n'.format(path, host)
    # request和response都是bytes格式，发送前需要转换
    encoding = 'utf-8'
    s.send(request.encode(encoding))

    # 这里是服务器的工作时间，它会接收到request并解析需求，拿出对应数据组成response返回给可用户端

    response = response_by_socket(s)
    # response是bytes格式，解个码先
    r = response.decode(encoding)
    # 解析response
    status_code, headers, body = parsed_response(r)
    # 豆瓣网站是加密的，我们如果填写的为http，那么服务器会返回一个301，并且header里会有Location: xxxxxxx的字段告诉跳转地址
    if status_code == 301:
        url = headers['Location']
        return get(url)

    return status_code, headers, body


def main():
    url = 'http://movie.douban.com/top250?start=25&filter='
    status_code, headers, body = get(url)
    print(status_code, headers, body)


# 测试parsed_url
def test_parsed_url():
    http = 'http'
    https = 'https'
    host = 'g.cn'
    path = '/'
    test_items = [
        ('http://g.cn', (http, host, 80, path)),
        ('http://g.cn/', (http, host, 80, path)),
        ('http://g.cn:90', (http, host, 90, path)),
        ('http://g.cn:90/', (http, host, 90, path)),
        #
        ('https://g.cn', (https, host, 443, path)),
        ('https://g.cn:233/', (https, host, 233, path)),
    ]
    for t in test_items:
        url, expected = t
        u = parsed_url(url)
        assert u == expected, "parsed_url error, {} || {} || {}".format(url, u, expected)


# 测试parsed_response
def test_parsed_response():
    response = 'HTTP/1.1 301 Moved Permanently\r\n' \
               'Content-Type: text/html\r\n' \
               'Location: https://movie.douban.com/top250\r\n' \
               'Content-Length: 178\r\n\r\n' \
               'test body'
    status_code, header, body = parsed_response(response)
    assert status_code == 301
    assert len(list(header.keys())) == 3
    assert body == 'test body'


# 测试是否能正确处理 HTTP 和 HTTPS
def test_get():
    urls = [
        'http://movie.douban.com/top250',
        'https://movie.douban.com/top250',
    ]
    for u in urls:
        get(u)


def test():
    test_parsed_url()
    test_get()
    test_parsed_response()


if __name__ == '__main__':
    # test()
    main()
