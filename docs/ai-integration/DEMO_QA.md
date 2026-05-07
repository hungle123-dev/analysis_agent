# Demo And Q&A

## Kich ban demo 5-7 phut

1. Mo dashboard/module AI.
2. Chon dataset.
3. Hien schema cot de chung minh AI chi biet cot co that.
4. Nhap cau: "Hay goi y 3 huong phan tich cho dataset nay".
5. Chon mot goi y va yeu cau AI tao code.
6. Chi ra code dang `pending_review`, chua chay.
7. Sua mot tham so trong code.
8. Bam `Approve`.
9. Bam `Run locally`.
10. Hien table/chart/stdout.
11. Mo Logs va tim lai trace vua demo.

## Cau hoi phan tich nen chuan bi

So cau hoi toi thieu bang so thanh vien trong nhom.

1. Goi y cac huong phan tich dua tren dataset.
2. Kiem tra null count va de xuat cach xu ly.
3. Ve bieu do xu huong theo thoi gian.
4. So sanh top 10 nhom co gia tri cao nhat.
5. Ve boxplot de phat hien outlier.
6. Tao heatmap correlation cho cot so.
7. Giai thich mot bieu do da tao.
8. Sua code de doi loai bieu do.

## Cau hoi ngoai le thay co the hoi

### AI co tu chay code khong?

Khong. AI chi tao proposal. Code phai duoc hien thi, nguoi dung sua/approve, execution API moi chay.

### Neu AI bia so lieu thi sao?

Prompt va schema cam AI bia so lieu. Neu chua co artifact ket qua, AI chi duoc tao code de tinh, khong duoc tu ket luan.

### Neu AI dung sai ten cot?

Backend co dataset context va validator. Proposal dung cot khong ton tai se bi reject hoac yeu cau AI tao lai.

### Neu code nguy hiem?

Policy checker chan import/ham nguy hiem. UI van hien code cho nguoi dung xem. Execution API chi chay code da approve va da qua checker.

### Neu code chay qua lau?

Runner co timeout. Neu qua timeout, run chuyen `failed` va stderr/log duoc luu.

### Vi sao can Logs API?

Logs API dung de truy xuat lai toan bo qua trinh su dung AI: request, code, nguoi approve, ket qua, loi va explanation. Day cung la bang chung cho bao cao.

## Checklist truoc khi nop

- Co it nhat 1 dataset demo.
- Co UI nhap request.
- Co UI hien va sua code.
- Co approve button.
- Co run local.
- Co output chart/table.
- Co logs truy xuat lai.
- Co it nhat so cau hoi demo bang so thanh vien nhom.
- Co mot case code bi chan vi chua approve hoac vi pham policy.

## Cau noi ngan gon khi gioi thieu

> Module AI cua nhom hoat dong nhu mot tro ly phan tich co kiem soat. AI giup de xuat va viet code, nhung khong tu thuc thi. Nguoi dung xem, sua, phe duyet, sau do code moi chay local va moi buoc deu duoc luu log.
