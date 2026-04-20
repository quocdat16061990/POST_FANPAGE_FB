import os
import requests
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# CẤU HÌNH GOOGLE SHEET
# ==========================================
SHEET_ID = "1SFAr1CFMzMPQXFToZEAwA2U1FaHpeCQqv7CyMa-f-0w"
# Lấy đúng file credentials nằm trong folder SELENIUM_ZALO như file tham khảo
CREDENTIALS_FILE = "/home/ubuntu/SELENIUM_ZALO/gen-lang-client-0450618162-54ea7d476a02.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# Thư mục chứa ảnh: Dùng thư mục riêng
IMAGE_DIRS = [
    "/home/ubuntu/PostFacebookDocument/images"
]

# ==========================================
# CẤU HÌNH FACEBOOK FANPAGE (Đăng Bài API)
# ==========================================
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "112842958429935")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "EAAXNgTlloaQBRLwtRwfQ6tdlMPdZCH4A3hX9IaNYhJH6ukk7vTnoRFykUZCl7To2RtRCOAgvofScgfAkCue8C5aolNIsnpZAZAVWN3dSVpE3HxiZB99mehpp5nqMEWO4rGACGgRTh7px5pbBmQPiA9UZBwrDWPT5KlU24VfLVXk64JPuEu2ZAA3a7TXxZClAcX8MEY8TlDPLXfEHIqJ9T3gNv8MZD")


def find_image_path(img_name: str) -> str:
    """Tìm đường dẫn thực tế của ảnh dựa trên tên file và các thư mục cấu hình."""
    if not img_name or str(img_name).strip().lower() == 'nan':
        return ""
        
    img_name = str(img_name).strip()
    # Nếu là đường dẫn tuyệt đối hoặc nằm ở thư mục hiện tại
    if os.path.exists(img_name):
        return img_name
            
    possible_exts = ["", ".jpg", ".png", ".jpeg", ".webp"]
    for d in IMAGE_DIRS:
        if not os.path.exists(d): continue
        for ext in possible_exts:
            test_p = os.path.join(d, img_name + ext)
            if os.path.exists(test_p):
                return test_p
    return ""


def post_to_facebook_fanpage(content: str, image_path: str = "") -> dict:
    """Đăng bài viết (kèm ảnh nếu có) lên Facebook Fanpage."""
    params = {"access_token": FB_PAGE_ACCESS_TOKEN}
    
    if image_path:
        # Nếu có ảnh, dùng endpoint /photos
        url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
        data = {"caption": content}
        print(f"[Facebook] Đang đăng bài KÈM ẢNH '{image_path}' lên Fanpage...")
        
        with open(image_path, "rb") as img_file:
            files = {"source": img_file}
            response = requests.post(url, params=params, data=data, files=files, timeout=60)
            
    else:
        # Nếu không có ảnh, dùng endpoint /feed
        url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
        data = {"message": content}
        print(f"[Facebook] Đang đăng bài CHỈ CÓ TEXT lên Fanpage...")
        
        response = requests.post(url, params=params, data=data, timeout=60)
        
    if not response.ok:
        raise RuntimeError(f"Lỗi khi gọi Fanpage API: {response.text}")
        
    return response.json()


def main():
    print("========================================")
    print("VẬN HÀNH AUTO ĐĂNG BÀI FACEBOOK FANPAGE")
    print("========================================")
    
    print("Đang kết nối tới Google Sheet...")
    try:
        credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        gc = gspread.authorize(credentials)
        workbook = gc.open_by_key(SHEET_ID)
        
        try:
            worksheet = workbook.worksheet("Fanpage")
        except:
            print("Không tìm thấy tab 'Fanpage', đang dùng ưu tiên tab đầu tiên...")
            worksheet = workbook.sheet1
            
        records = worksheet.get_all_records()
        headers = worksheet.row_values(1)
        
        # Tạo cột 'Status' nếu chưa có trong Sheet
        if 'Status' not in headers:
            status_col = len(headers) + 1
            worksheet.update_cell(1, status_col, 'Status')
            headers = worksheet.row_values(1)
            
        status_col_index = headers.index('Status') + 1

        print(f"Đã tải {len(records)} dòng trạng thái từ Google Sheet.")
        
        for idx, row in enumerate(records):
            row_num = idx + 2
            
            tieu_de = str(row.get('Tiêu Đề', '')).strip()
            noi_dung = str(row.get('Mô Tả', row.get('Nội Dung', ''))).strip()
            anh = str(row.get('Images', row.get('Hình ảnh', row.get('Hình Ảnh', '')))).strip()
            status = str(row.get('Status', '')).strip()
            
            # Xử lý trường hợp chuỗi trống / nan
            if tieu_de.lower() == 'nan': tieu_de = ""
            if noi_dung.lower() == 'nan': noi_dung = ""
            
            # CHỈ ĐĂNG bài có trạng thái UNAPPROVED
            if status == 'UNAPPROVED' and (tieu_de or noi_dung):
                print(f"\n=> Đang xử lý Bài viết UNAPPROVED ở dòng {row_num}")
                
                # Gộp Tiêu đề và Nội dung
                full_content = ""
                if tieu_de: full_content += tieu_de + "\n\n"
                if noi_dung: full_content += noi_dung
                
                # Tìm đường dẫn thực tế của ảnh
                real_image_path = find_image_path(anh)
                if anh and not real_image_path:
                    print(f"⚠️ Cảnh báo: Không thể tìm thấy file ảnh gốc '{anh}' trên server. Sẽ đăng tin không kèm ảnh!")
                
                # Tiến hành đăng lên Fanpage API
                try:
                    fb_result = post_to_facebook_fanpage(full_content, real_image_path)
                    post_id = fb_result.get('post_id') or fb_result.get('id')
                    print(f"✅ Đăng thành công! ID Bài viết Fanpage: {post_id}")
                    
                    # Update lại Google Sheet
                    worksheet.update_cell(row_num, status_col_index, 'APPROVED')
                    print(f"✅ Đã cập nhật trạng thái 'APPROVED' trên dòng {row_num}.")
                    
                    # Kết thúc: chỉ đăng 1 bài một lần
                    print("\n--- HOÀN TẤT ĐĂNG 1 BÀI VIẾT ---")
                    break
                    
                except Exception as e:
                    print(f"❌ Lỗi khi tải ảnh/đăng bài (dòng {row_num}): {e}")
                    
    except Exception as e:
        print(f"❌ Lỗi cấu hình tải Sheet/API hệ thống: {e}")

if __name__ == "__main__":
    main()
