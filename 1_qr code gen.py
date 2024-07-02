import qrcode

whatsapp_url = "https://wa.me/7397250247"


qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
qr.add_data(whatsapp_url)
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
img.save("whatsapp_qr.png")
