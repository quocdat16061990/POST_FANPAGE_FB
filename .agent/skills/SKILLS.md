# Skill: Tự động hóa đăng bài viết lên Facebook Fanpage qua API (Fanpage Auto Poster)

Bộ skill này hướng dẫn cách cài đặt và vận hành một công cụ tự động hóa đăng bài viết và đính kèm ảnh lên Facebook Fanpage thông qua API chính thức (Graph API) bằng Python. Trọng tâm của dự án là không dùng giao diện giả lập mà sử dụng hoàn toàn API của Facebook.

---

## 1. Mục đích và Các Khái Niệm Quan Trọng

- **Tính Năng**: Bot tự động quét dữ liệu từ Google Sheets (danh sách bài đăng có nội dung, hình ảnh), sử dụng Facebook Graph API để đăng bài lên Fanpage, sau đó tự động cập nhật trạng thái đã đăng thành công/thất bại vào lại Google Sheets.
- **Sử Dụng API Chính Chủ**: Việc dùng Facebook Graph API có ưu điểm tuyệt đối so với giả lập trình duyệt (Selenium): Tốc độ cực nhanh, không qua màn hình, hoạt động ngầm hoàn toàn và không lo bị khóa tài khoản do hành vi chuột.

---

## 2. Triển Khai Trên Máy Mới (Từ A đến Z)

### Bước 0: Clone repo về máy
Nếu **chưa có** thư mục dự án trên máy:
```powershell
git clone https://github.com/quocdat16061990/POST_FANPAGE_FB.git
cd POST_FANPAGE_FB
```

### Bước 1: BẮT BUỘC - Chuẩn bị file JSON Service Account (Google)

> ⚠️ **KHÔNG CÓ FILE NÀY THÌ BOT KHÔNG ĐỌC ĐƯỢC SHEET!**

File JSON này là chìa khóa để Bot đọc/ghi dữ liệu ở Google Sheets:
1. Vào [Google Cloud Console](https://console.cloud.google.com/), tạo **Service Account** với quyền quản lý Google Sheets API.
2. Tạo và tải xuống file **JSON key** cho Service Account đó.
3. **Copy file JSON vào thư mục gốc** của dự án.
4. **Share Google Sheet cho email của Service Account**: Mở bảng tính Google Web, nhấn nút Share và paste địa chỉ email `client_email` lấy từ file JSON (VD: `bot-abc@project-xyz.iam.gserviceaccount.com`) vào, cấp quyền **Editor**.

### Bước 1.1: BẮT BUỘC - Chuẩn bị Page Access Token của Facebook Fanpage

> ⚠️ **CẦN KẾT NỐI FACEBOOK GRAPH API ĐỂ ĐĂNG BÀI:**

1. Vào [Facebook Developers](https://developers.facebook.com/), tạo/cấp quyền App và tạo **Page Access Token** vĩnh viễn (hoặc dài hạn) của Fanpage bạn muốn bot tự đăng.
2. Lấy **Page ID** của Fanpage.
3. Đặt các khóa này vào file môi trường (`.env`) hoặc khai báo biến. Ví dụ:
   ```env
   PAGE_ACCESS_TOKEN=token_cua_ban_o_day
   PAGE_ID=id_fanpage_cua_ban
   ```

### Bước 2: Cài đặt Python và tạo môi trường ảo

```powershell
# 1. Kiểm tra Python đã cài chưa
python --version

# 2. Tạo môi trường ảo (chỉ làm 1 lần)
py -m venv venv

# 3. Kích hoạt môi trường ảo
.\venv\Scripts\Activate.ps1
# Hoặc dùng CMD: .\venv\Scripts\activate.bat

# 4. Cài toàn bộ thư viện cần thiết
pip install --upgrade pip
pip install requests gspread pandas oauth2client pyinstaller python-dotenv
```
*(Ghi chú: Thư viện `requests` dùng để gọi Facebook API, còn lại là xử lý Sheet).*

### Bước 3: Chuẩn bị thư mục images

- **Thư mục images**: Tạo một thư mục `images/` ở ngay gốc dự án. Mọi file ảnh cần đăng sẽ để vào đây. Tên ảnh cần khớp với khai báo trên Sheet (vd khai `anh-san-pham` trên Sheet thì phải có file `anh-san-pham.png` hoặc `.jpg` trong thư mục này).

---

## 3. Cách Khởi Chạy (Run Chương Trình)

### Option A: Chạy trực tiếp qua Source
```powershell
.\venv\Scripts\python.exe main.py
```
*(Tên file `main.py` thay bằng file code chính của chương trình)*

### Option B: Build file .exe chạy thực tế

Build một lần, click đúp file `.exe` sử dụng độc lập (không cần cài Python):

```powershell
.\venv\Scripts\pyinstaller.exe --onefile --distpath . main.py
```

> ⚠️ **Lưu ý quan trọng khi dùng file .exe**:
> - File `.exe` phải đặt **cùng cấp** với file JSON credentials, thư mục `images/` và file `.env`.
> - Thư mục `build/` sinh ra sau build có thể xóa.

---

## 4. Cấu Hình Google Sheet Quản Lý Bài Đăng

Sheet quản lý (Worksheet dự kiến) cần có các cột:

| Cột | Mô tả |
|-----|-------|
| `Tiêu Đề` | Tiêu đề của bài viết (có thể dùng để nhận diện nhanh trong file hoặc làm dòng đầu tiên) |
| `Mô Tả` | Nội dung văn bản (Caption) sẽ đăng lên Fanpage. Có thể chứa emoji hoặc xuống dòng |
| `Images` | Tên tệp ảnh đại diện cần tải lên (Ví dụ: `khung_anh_1` => tìm trong `/images/khung_anh_1.jpg`) |
| `Status` | Trạng thái xử lý: `PENDING` (chờ gửi), `SUCCESS` (đã đăng), `ERROR` (lỗi up api) |

> Bot quét Google Sheet lọc các dòng `Status = PENDING`. Gửi Graph API báo kết quả về. Tùy HTTP Status Code sẽ cập nhật giá trị vào `Status`.

---

## 5. API Logic - Các Endpoints Cơ Bản Cần Tham Khảo

Sử dụng thư viện `requests` để tương tác:

- **Đăng trạng thái chỉ có text**:
  ```http
  POST https://graph.facebook.com/v19.0/{PAGE_ID}/feed
  ```
  Truyền tham số `message=<Nội Dung>` và `access_token=<PAGE_ACCESS_TOKEN>`

- **Đăng bài kèm ảnh**:
  ```http
  POST https://graph.facebook.com/v19.0/{PAGE_ID}/photos
  ```
  Thông thường cần truyền `message=<Caption>` và đính kèm `source` ở dạng tập tin (multipart file stream), và tất nhiên `access_token`.

---

## 6. Gitignore Khuyến Nghị

```gitignore
# PyInstaller
build/
dist/
*.spec
*.exe

# Keys & Auth (Tuyệt đối không đẩy lên repo public!)
*.json
.env

# Virtual Environment
venv/
__pycache__/
```
