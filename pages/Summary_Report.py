from io import BytesIO
import pandas as pd
import streamlit as st
import sqlite3

# --- LETAKKAN DI BARIS PALING ATAS SETELAH IMPORT ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("⚠️ Anda belum login. Silakan login terlebih dahulu melalui halaman utama (app.py).")
    st.stop()

# Import untuk PDF Generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Summary Report Pengaduan HI", page_icon="📊", layout="wide")
conn = sqlite3.connect("database.db", check_same_thread=False)

st.title("📊 Summary Report & Rekapitulasi Pengaduan HI")
st.markdown("---")

df = pd.read_sql_query("SELECT * FROM tabel_pengaduan", conn)

if not df.empty:
    # --- TABEL REKAPITULASI & EKSPOR EXCEL ---
    st.subheader("📋 Tabel Rekapitulasi Keseluruhan Data")
    
    output_excel = BytesIO()
    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Rekap_Pengaduan")
    
    st.download_button(
        label="📥 Ekspor Rekapitulasi ke Excel",
        data=output_excel.getvalue(),
        file_name="Rekapitulasi_Pengaduan_HI.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.dataframe(df, use_container_width=True)
    st.markdown("---")

    # --- LIHAT DETAIL & DOWNLOAD PDF BERDASARKAN ID ---
    st.subheader("🔍 Lihat Detail Lengkap & Unduh Laporan PDF Berdasarkan ID")
    
    id_list = df["id_pengaduan"].tolist()
    selected_id = st.selectbox("Pilih ID Pengaduan:", id_list)
    
    if selected_id:
        row_detail = df[df["id_pengaduan"] == selected_id].iloc[0]
        
        st.info(f"Menampilkan Detail Lengkap untuk ID: **{selected_id}**")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.write(f"**Tanggal Masuk:** {row_detail.get('tanggal_masuk', '-')}")
            st.write(f"**Kategori:** {row_detail.get('kategori', '-')}")
            st.write(f"**Pelapor / Pemohon:** {row_detail.get('pelapor', '-')}")
            st.write(f"**Alamat Pelapor:** {row_detail.get('alamat', '-')}")
            st.write(f"**No. Telepon Pelapor:** {row_detail.get('no_telp', '-')}")
            st.write(f"**Perihal:** {row_detail.get('perihal', '-')}")
        with col_d2:
            st.write(f"**Terlapor / Perusahaan:** {row_detail.get('terlapor', '-')}")
            st.write(f"**Alamat Terlapor:** {row_detail.get('alamat_terlapor', '-')}")
            st.write(f"**No. Telepon Terlapor:** {row_detail.get('no_telp_terlapor', '-')}")
            st.write(f"**Mediator:** {row_detail.get('mediator', '-')}")
            st.write(f"**Status Berjalan:** {row_detail.get('status', '-')}")
            st.write(f"**Catatan / Keterangan:** {row_detail.get('catatan', '-')}")

        st.markdown("---")

        def generate_pdf(data):
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            story = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'TitleStyle',
                parent=styles['Heading1'],
                fontSize=16,
                alignment=1,
                textColor=colors.HexColor("#2c3e50")
            )
            
            story.append(Paragraph(f"LAPORAN DETAIL PENGADUAN HI", title_style))
            story.append(Paragraph(f"ID Pengaduan: {data.get('id_pengaduan', '-')}", styles['Normal']))
            story.append(Spacer(1, 15))
            
            pdf_data = [
                ["Field / Kolom", "Keterangan Detail"],
                ["ID Pengaduan", str(data.get('id_pengaduan', '-'))],
                ["Tanggal Masuk", str(data.get('tanggal_masuk', '-'))],
                ["Perihal", str(data.get('perihal', '-'))],
                ["Kategori", str(data.get('kategori', '-'))],
                ["Pelapor", str(data.get('pelapor', '-'))],
                ["Alamat Pelapor", str(data.get('alamat', '-'))],
                ["No. Telp Pelapor", str(data.get('no_telp', '-'))],
                ["Terlapor", str(data.get('terlapor', '-'))],
                ["Alamat Terlapor", str(data.get('alamat_terlapor', '-'))],
                ["No. Telp Terlapor", str(data.get('no_telp_terlapor', '-'))],
                ["Mediator", str(data.get('mediator', '-'))],
                ["Status Penanganan", str(data.get('status', '-'))],
                ["Tanggal Selesai", str(data.get('sa_tanggal', '-'))],
                ["Pilihan Penyelesaian", str(data.get('sa_pilihan', '-'))],
                ["Catatan Tambahan", str(data.get('catatan', '-'))]
            ]
            
            t = Table(pdf_data, colWidths=[150, 350])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (1, 0), colors.HexColor("#3498db")),
                ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            story.append(t)
            doc.build(story)
            pdf_buffer.seek(0)
            return pdf_buffer.getvalue()

        pdf_bytes = generate_pdf(row_detail)
        st.download_button(
            label=f"📄 Unduh Laporan PDF untuk ID {selected_id}",
            data=pdf_bytes,
            file_name=f"Laporan_Pengaduan_{selected_id}.pdf",
            mime="application/pdf",
            type="primary"
        )
else:
    st.info("Belum ada data pengaduan yang tersimpan di dalam database.")
