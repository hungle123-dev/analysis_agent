import pandas as pd
import numpy as np

def preprocess_real_estate_data():
    print("1. Đang đọc dữ liệu...")
    df_buy = pd.read_csv('house_buying_dec29th_2025.csv')
    df_rent = pd.read_csv('house_rental_dec29th_2025.csv')
    
    # 1. Thêm nhãn phân loại và gộp 2 file làm 1
    df_buy['listing_type'] = 'Mua Bán'
    df_rent['listing_type'] = 'Cho Thuê'
    df = pd.concat([df_buy, df_rent], ignore_index=True)
    
    print(f"Tổng số dòng ban đầu: {len(df)}")

    # 2. Xử lý cột vị trí (Location) -> Tách Tỉnh/Thành và Quận/Huyện
    print("2. Đang xử lý địa lý (Location)...")
    def extract_city(loc):
        parts = str(loc).split(',')
        return parts[-1].strip() if len(parts) > 1 else 'Chưa xác định'

    def extract_district(loc):
        parts = str(loc).split(',')
        return parts[-2].strip() if len(parts) > 1 else parts[0].strip()

    df['city_province'] = df['location'].apply(extract_city)
    df['district'] = df['location'].apply(extract_district)

    # 3. Ép kiểu dữ liệu và xử lý Missing/Outliers
    print("3. Đang làm sạch dữ liệu số...")
    num_cols =['area_m2', 'bedrooms', 'bathrooms', 'floors', 'price_million_vnd']
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce') # Chữ lỗi biến thành NaN

    # Xóa các dòng có diện tích hoặc giá bị Null, hoặc nhỏ hơn/bằng 0 (dữ liệu rác)
    df = df.dropna(subset=['price_million_vnd', 'area_m2'])
    df = df[(df['price_million_vnd'] > 0) & (df['area_m2'] > 0)]

    # Điền giá trị 0 cho các cột số lượng phòng/tầng nếu bị trống
    df[['bedrooms', 'bathrooms', 'floors']] = df[['bedrooms', 'bathrooms', 'floors']].fillna(0)

    # Chuẩn hóa cột Frontage (mặt tiền) về True/False rõ ràng
    df['frontage'] = df['frontage'].astype(str).str.upper().map({'TRUE': True, 'FALSE': False})
    df['frontage'] = df['frontage'].fillna(False)

    # 4. Feature Engineering: Tính Giá / m2 (Triệu VNĐ/m2)
    print("4. Đang tạo thêm biến (Giá / m2)...")
    df['price_per_m2'] = round(df['price_million_vnd'] / df['area_m2'], 2)

    # 5. Dọn dẹp cột không cần thiết và sắp xếp lại
    print("5. Đang xuất file...")
    # Xóa cột id và detail_url để giảm dung lượng file vì không cần thiết cho phân tích
    cols_to_drop =['id', 'detail_url', 'location'] 
    df_cleaned = df.drop(columns=[col for col in cols_to_drop if col in df.columns])

    # Đổi tên cột sang tieng Việt cho đồng nhất
    df_cleaned.rename(columns={
        'title': 'Tieu_De',
        'timeline_h': 'Thoi_Gian_Dang_Gio',
        'area_m2': 'Dien_Tich_m2',
        'bedrooms': 'So_Phong_Ngu',
        'bathrooms': 'So_Phong_Tam',
        'floors': 'So_Tang',
        'frontage': 'Mat_Tien',
        'price_million_vnd': 'Gia_Trieu_VND',
        'listing_type': 'Loai_Hinh',
        'city_province': 'Tinh_Thanh',
        'district': 'Quan_Huyen',
        'price_per_m2': 'Gia_Tren_m2_Trieu'
    }, inplace=True)

    # Lưu ra file cuối cùng
    output_file = 'cleaned_vietnam_real_estate.csv'
    df_cleaned.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"Xử lý thành công! File xuất ra: {output_file} | Tổng số dòng hợp lệ: {len(df_cleaned)}")
    return df_cleaned

# Chạy hàm
if __name__ == "__main__":
    preprocess_real_estate_data()