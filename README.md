# PTTfeeds

Monitor PTT for interesting new posts with specified authors.

這是一個PTT發文追蹤器。他會透過PTT web介面，定期抓取最新的發文，當發文內容符合使用者定義的規則時，便會寄信通知。（注意，PTT web版的更新大約有五分鐘的延遲）

## Installation

```console
$ sh -c "$(curl -fsSL https://raw.githubusercontent.com/dacapo1142/PTTfeeds/master/install.sh)"
```

## Usage

```console
$ cd PTTfeeds && python server.py
```

## Setting

使用者可以自行定義通知的規則，其定義放置於`settings.json`中。（若查無此檔，程式將自行建立）

Example

```json
{
    "gmail_user_id": "sender",
    "boards": {
        "Test": [{
            "subscribers": ["sub1@gmail.com"],
            "author": "author1",
            "title": ["a", "b", "c"]
        }, {
            "subscribers": ["sub2@gmail.com", "sub3@gmail.com"],
            "title": ["aaa"],
            "content": ["123", "321"]
        }]
    }
}

```
`gmail_user_id`代表了用以寄送email的gmail信箱帳號，範例為`sender`，故寄信地址為`sender@gmail.com`。
當在`Test`版出現新文章，其「作者為`author1`」且「標題包含`a`或`b`或`c`」便會寄信通知`sub1@gmail.com`；當出現「標題包含`aaa`」且「內容包含`123`或`321`」時，寄信通知`sub2@gmail.com`與`sub3@gmail.com`。