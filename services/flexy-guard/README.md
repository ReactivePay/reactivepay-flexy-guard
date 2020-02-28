## Check request

You can send any JSON formatted plain POS request to **api/check**

Payment request example:

```
{
  "amount": 9000,
  "mid": "123",
  "userid": "213123123",
  "email": "ikik4@yandex.ru",
  "postcode": "123123123",
  "btc_address": "kjr2u4y2938dshakr3298hwejry2983yh",
  "tid": "123123",
  "acq_id": "1234",
  "status": "decline",
  "ip": "109.252.25.138",
  "currency": "USD",
  "card": "qwe31221312312312rty",
  "bin": "527883",
  "order": "123123123123",
  "order_description": "wdfssdasdasdasd",
  "firstName": "vladimir",
  "lastName": "kovalevskiy",
  "address1": "address1",
  "address2": "address2",
  "city": "Toronto",
  "phone": "1234567890",
  "m_phone": "abcd",
  "shippingAddress": "sadasdsa 1231",
  "personalAddress": "asdadas 12312 sdasd",
  "mcc": "6012",
  "company_id": "213123213"
}

```

## MongoDB configuaration
```
mongod --replSet rs0 --bind_ip 0.0.0.0
mongo>rs.initiate()
mongo>use counters
mongo>db.rules.createIndex({Comment: "text", HashDescr: "text"})
```

## Import BIN/IP database

Import IP/BIN country databases from flexy-guard root folder

```
tr ";" "\t" < rules/lists/ip2country_iso.csv | mongoimport --host [HOSTNAME] --port [PORT] --db counters --collection ip:country --drop --type tsv --headerline

tr ";" "\t" < rules/lists/bins_iso_13_2.csv | mongoimport --host [HOSTNAME] --port [PORT]  --db counters --collection bin:countries --drop --type tsv --headerline

```