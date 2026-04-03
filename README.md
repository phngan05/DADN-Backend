# Khởi tạo Backend
## Tạo môi trường ảo
- Tạo thư mục venv chứa môi trường ảo
```sh
python -m venv venv
```
- Kích hoạt
Windows
```sh
venv/Scripts/activate
```

MacOS/Linux
```sh
source venv/bin/activate
```

## Cài đặt các module cần thiết
```sh
pip install -r requirements.txt
```

## Chạy API

```sh
uvicorn app.main:app --reload
```

# API Address
Truy cập [FastAPI docs](http://127.0.0.1:8000/docs) sau khi khởi tạo để dễ xem request body hoặc parameter 

- /auth
    + post /login: đăng nhập
    + post /register: đăng ký
    
- /user
    + get / : lấy full_name và username
    + put / : cập nhật thông tin user

- /record: cho các feed trong adafruit
    + get /all: lấy giá trị mới nhất từ tất cả các feed trong Adafruit IO
    + get /history/{feed_key}: lấy lịch sử của một feed nào đó để vẽ biểu đồ
    + put / : cập nhật giá trị một bảng nào đó

- /feed: thông tin các feed trong supabase
    + get / : lấy thông tin
    + put / : cập nhật
    + post / : tạo thông tin feed mới
