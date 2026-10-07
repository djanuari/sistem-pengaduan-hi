from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from supabase import Client, create_client
import streamlit as st

if not st.session_state.get("logged_in"):
    st.warning("Silakan login terlebih dahulu.")
    st.stop()

st.title("Monitoring Kepesertaan Berdasarkan Jenjang Pendidikan")
st.write("Rekapitulasi jumlah satuan pendidikan, PTK, serta rincian daftar sekolah.")

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

def create_pdf_report(df, title_text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Heading1"], fontSize=14, alignment=1, spaceAfter=15)
    
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 10))
    
    table_data = [list(df.columns)]
    for _, row in df.iterrows():
        table_data.append([str(val) for val in row.values])
        
    t = Table(table_data)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), (0.2, 0.4, 0.6)),
        ("TEXTCOLOR", (0, 0), (-1, 0), (1, 1, 1)),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), (0.95, 0.95, 0.95)),
        ("GRID", (0, 0), (-1, -1), 0.5, (0.5, 0.5, 0.5)),
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

list_jenjang = [
    "PAUD", "Kelompok Bermain (KB)", "Taman Kanak-Kanak (TK)", 
    "Sekolah Dasar (SD)", "Sekolah Menengah Pertama (SMP)", 
    "Sekolah Menengah Atas (SMA)", "Sekolah Menengah Kejuruan (SMK)", 
    "Sekolah Luar Biasa (SLB)", "Lembaga Kursus", "Pendidikan Tinggi"
]

tab1, tab2, tab3, tab4 = st.tabs([
    "Tabel Rekapitulasi Utama", 
    "Input & Daftar Detail Sekolah", 
    "Rincian per Jenjang Pendidikan", 
    "Grafik Persentase"
])

with tab1:
    st.subheader("Rekapitulasi Satuan Pendidikan dan PTK")
    try:
        res = supabase.table("tabel_rekap_pendidikan").select("*").order("id", desc=False).execute()
        df_rekap = pd.DataFrame(res.data)
        
        if not df_rekap.empty:
            if "sudah_terdaftar" in df_rekap.columns and "jumlah_ptk" in df_rekap.columns:
                df_rekap["Belum Terdaftar"] = df_rekap["jumlah_ptk"] - df_rekap["sudah_terdaftar"]
                
                tot_satuan = df_rekap["jumlah_satuan_pendidikan"].sum() if "jumlah_satuan_pendidikan" in df_rekap.columns else 0
                tot_ptk = df_rekap["jumlah_ptk"].sum()
                tot_sudah = df_rekap["sudah_terdaftar"].sum()
                tot_belum = df_rekap["Belum Terdaftar"].sum()
                tot_persen = round((tot_sudah / tot_ptk * 100) if tot_ptk > 0 else 0, 2)
                
                df_rekap["Persentase"] = (df_rekap["sudah_terdaftar"] / df_rekap["jumlah_ptk"].replace(0, 1)) * 100
                df_rekap["Persentase"] = df_rekap["Persentase"].round(2).astype(str) + "%"
                
                row_total = {
                    "jenjang": "TOTAL KESELURUHAN",
                    "jumlah_satuan_pendidikan": tot_satuan,
                    "jumlah_ptk": tot_ptk,
                    "sudah_terdaftar": tot_sudah,
                    "Belum Terdaftar": tot_belum,
                    "Persentase": f"{tot_persen}%"
                }
                for col in df_rekap.columns:
                    if col not in row_total:
                        row_total[col] = ""
                        
                df_rekap_display = pd.concat([df_rekap, pd.DataFrame([row_total])], ignore_index=True)
            else:
                df_rekap_display = df_rekap.copy()
                
            df_rekap_display = df_rekap_display.drop(columns=["created_at"], errors="ignore")
            st.dataframe(df_rekap_display, use_container_width=True, hide_index=True)
            
            # --- FITUR EDIT JUMLAH SATUAN PENDIDIKAN & PTK ---
            st.markdown("---")
            with st.expander("✏️ Edit Jumlah Satuan Pendidikan & Total PTK per Jenjang"):
                with st.form("form_edit_rekap"):
                    pilih_j_edit = st.selectbox("Pilih Jenjang yang Ingin Diubah:", list_jenjang)
                    
                    # Ambil data awal untuk default value di form
                    current_row = df_rekap[df_rekap["jenjang"] == pilih_j_edit]
                    default_satuan = int(current_row["jumlah_satuan_pendidikan"].values[0]) if not current_row.empty and "jumlah_satuan_pendidikan" in current_row.columns else 0
                    default_ptk = int(current_row["jumlah_ptk"].values[0]) if not current_row.empty and "jumlah_ptk" in current_row.columns else 0
                    
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        new_jumlah_satuan = st.number_input("Jumlah Satuan Pendidikan Baru", min_value=0, value=default_satuan)
                    with col_e2:
                        new_jumlah_ptk = st.number_input("Jumlah Total PTK Baru", min_value=0, value=default_ptk)
                        
                    submit_edit_rekap = st.form_submit_button("Simpan Perubahan Rekap", type="primary")
                    
                    if submit_edit_rekap:
                        try:
                            supabase.table("tabel_rekap_pendidikan").update({
                                "jumlah_satuan_pendidikan": new_jumlah_satuan,
                                "jumlah_ptk": new_jumlah_ptk
                            }).eq("jenjang", pilih_j_edit).execute()
                            
                            st.success(f"Data rekap untuk jenjang **{pilih_j_edit}** berhasil diperbarui!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal memperbarui rekap: {e}")
            # ------------------------------------------------

            st.markdown("---")
            st.subheader("Unduh Laporan Rekapitulasi")
            
            col_dl1, col_dl2, col_dl3 = st.columns(3)
            with col_dl1:
                csv_data = df_rekap_display.to_csv(index=False).encode("utf-8")
                st.download_button("Unduh CSV", data=csv_data, file_name="rekap_monitoring_bpjs.csv", mime="text/csv")
            with col_dl2:
                output_excel = BytesIO()
                with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
                    df_rekap_display.to_excel(writer, index=False, sheet_name="Rekap BPJS")
                excel_data = output_excel.getvalue()
                st.download_button("Unduh Excel", data=excel_data, file_name="rekap_monitoring_bpjs.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            with col_dl3:
                pdf_data = create_pdf_report(df_rekap_display, "Laporan Rekapitulasi Monitoring BPJS Sektor Pendidikan")
                st.download_button("Unduh PDF", data=pdf_data, file_name="rekap_monitoring_bpjs.pdf", mime="application/pdf")
        else:
            st.info("Belum ada data rekap.")
    except Exception as e:
        st.error(f"Gagal memuat rekapitulasi: {e}")

with tab2:
    st.subheader("Pencatatan & Manajemen Nama Sekolah per Jenjang")
    
    with st.expander("Tambah Data Sekolah Baru", expanded=True):
        with st.form("form_detail_sekolah", clear_on_submit=True):
            pilih_jenjang = st.selectbox("Pilih Jenjang / Jenis Satuan Pendidikan", list_jenjang)
            nama_sekolah = st.text_input("Nama Sekolah / Lembaga")
            alamat_sekolah = st.text_area("Alamat Sekolah")
            
            col_tot, col1, col2 = st.columns(3)
            with col_tot:
                input_total_ptk = st.number_input("Jumlah Total PTK", min_value=0, value=0)
            with col1:
                input_sudah = st.number_input("Jumlah Sudah Terdaftar", min_value=0, value=0)
            with col2:
                input_belum = st.number_input("Jumlah Belum Terdaftar", min_value=0, value=0)
                
            keterangan_sekolah = st.text_input("Keterangan Tambahan")
            submit_sekolah = st.form_submit_button("Simpan Data Sekolah", type="primary")
            
            if submit_sekolah:
                if not nama_sekolah:
                    st.error("Nama sekolah wajib diisi!")
                else:
                    try:
                        data_sekolah = {
                            "jenjang": pilih_jenjang,
                            "nama_sekolah": nama_sekolah,
                            "alamat": alamat_sekolah,
                            "jumlah_total_ptk": input_total_ptk,
                            "jumlah_sudah": input_sudah,
                            "jumlah_belum": input_belum,
                            "keterangan": keterangan_sekolah
                        }
                        supabase.table("tabel_detail_sekolah").insert(data_sekolah).execute()
                        
                        if input_sudah > 0:
                            res_rekap = supabase.table("tabel_rekap_pendidikan").select("sudah_terdaftar").eq("jenjang", pilih_jenjang).execute()
                            if res_rekap.data:
                                current_val = res_rekap.data[0].get("sudah_terdaftar", 0) or 0
                                new_val = current_val + input_sudah
                                supabase.table("tabel_rekap_pendidikan").update({"sudah_terdaftar": new_val}).eq("jenjang", pilih_jenjang).execute()
                                
                        st.success("Data sekolah berhasil disimpan dan rekap diperbarui!")
                    except Exception as e:
                        st.error(f"Gagal menyimpan data sekolah: {e}")
                        
    st.markdown("---")
    st.subheader("Daftar Sekolah & Fitur Hapus Data")
    
    try:
        res_detail = supabase.table("tabel_detail_sekolah").select("*").order("id", desc=False).execute()
        df_detail = pd.DataFrame(res_detail.data)
        
        if not df_detail.empty:
            df_detail = df_detail.drop(columns=["created_at"], errors="ignore")
            pilih_filter = st.selectbox("Filter Berdasarkan Jenjang:", ["Semua Jenjang"] + list_jenjang)
            
            if pilih_filter != "Semua Jenjang":
                df_detail_filtered = df_detail[df_detail["jenjang"] == pilih_filter]
            else:
                df_detail_filtered = df_detail
                
            st.dataframe(df_detail_filtered, use_container_width=True, hide_index=True)
            
            st.markdown("### Hapus Data Sekolah")
            opsi_sekolah = {f"{row['nama_sekolah']} ({row['jenjang']}) - ID: {row['id']}": row['id'] for _, row in df_detail_filtered.iterrows()}
            
            if opsi_sekolah:
                pilih_hapus = st.selectbox("Pilih sekolah yang ingin dihapus:", list(opsi_sekolah.keys()))
                if st.button("Hapus Data Terpilih", type="secondary"):
                    target_id = opsi_sekolah[pilih_hapus]
                    data_hapus = supabase.table("tabel_detail_sekolah").select("*").eq("id", target_id).execute()
                    
                    if data_hapus.data:
                        item = data_hapus.data[0]
                        j_jenjang = item.get("jenjang")
                        j_sudah = item.get("jumlah_sudah", 0) or 0
                        
                        supabase.table("tabel_detail_sekolah").delete().eq("id", target_id).execute()
                        
                        if j_sudah > 0 and j_jenjang:
                            res_rekap = supabase.table("tabel_rekap_pendidikan").select("sudah_terdaftar").eq("jenjang", j_jenjang).execute()
                            if res_rekap.data:
                                current_val = res_rekap.data[0].get("sudah_terdaftar", 0) or 0
                                new_val = max(0, current_val - j_sudah)
                                supabase.table("tabel_rekap_pendidikan").update({"sudah_terdaftar": new_val}).eq("jenjang", j_jenjang).execute()
                                
                        st.success("Data sekolah berhasil dihapus dan rekapitulasi diperbarui!")
                        st.rerun()
            else:
                st.info("Tidak ada data pada filter jenjang ini.")
        else:
            st.info("Belum ada data detail sekolah yang diinput.")
    except Exception as e:
        st.info(f"Terjadi kesalahan saat memuat data detail: {e}")

with tab3:
    st.subheader("Rincian Rekapitulasi Berdasarkan Jenis Jenjang Pendidikan")
    pilih_jenjang_detail = st.selectbox("Pilih Jenjang Pendidikan:", list_jenjang, key="select_jenjang_detail")
    
    try:
        res_jenjang_terpilih = supabase.table("tabel_detail_sekolah").select("*").eq("jenjang", pilih_jenjang_detail).order("id", desc=False).execute()
        df_j_terpilih = pd.DataFrame(res_jenjang_terpilih.data)
        
        res_rekap_single = supabase.table("tabel_rekap_pendidikan").select("*").eq("jenjang", pilih_jenjang_detail).execute()
        
        st.markdown(f"### Ringkasan untuk Jenjang: **{pilih_jenjang_detail}**")
        if res_rekap_single.data:
            data_R = res_rekap_single.data[0]
            tot_satuan = data_R.get("jumlah_satuan_pendidikan", 0) or 0
            tot_ptk = data_R.get("jumlah_ptk", 0) or 0
            sudah_reg = data_R.get("sudah_terdaftar", 0) or 0
            belum_reg = max(0, tot_ptk - sudah_reg)
            persen_reg = round((sudah_reg / tot_ptk * 100) if tot_ptk > 0 else 0, 2)
            
            mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
            mcol1.metric("Jumlah Satuan", tot_satuan)
            mcol2.metric("Jumlah PTK", tot_ptk)
            mcol3.metric("Sudah Terdaftar", sudah_reg)
            mcol4.metric("Belum Terdaftar", belum_reg)
            mcol5.metric("Persentase", f"{persen_reg}%")
            
        st.markdown("---")
        st.markdown(f"**Daftar Sekolah / Lembaga pada Jenjang {pilih_jenjang_detail}:**")
        
        if not df_j_terpilih.empty:
            df_j_display = df_j_terpilih.drop(columns=["created_at"], errors="ignore")
            st.dataframe(df_j_display, use_container_width=True, hide_index=True)
            
            st.markdown("##### Unduh Laporan Jenjang Ini")
            dcol1, dcol2, dcol3 = st.columns(3)
            with dcol1:
                csv_j = df_j_display.to_csv(index=False).encode("utf-8")
                st.download_button("Unduh CSV", data=csv_j, file_name=f"rekap_{pilih_jenjang_detail.lower().replace(' ', '_')}.csv", mime="text/csv", key=f"csv_{pilih_jenjang_detail}")
            with dcol2:
                out_ex_j = BytesIO()
                with pd.ExcelWriter(out_ex_j, engine="openpyxl") as writer:
                    df_j_display.to_excel(writer, index=False, sheet_name=pilih_jenjang_detail[:30])
                ex_data_j = out_ex_j.getvalue()
                st.download_button("Unduh Excel", data=ex_data_j, file_name=f"rekap_{pilih_jenjang_detail.lower().replace(' ', '_')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"excel_{pilih_jenjang_detail}")
            with dcol3:
                pdf_j = create_pdf_report(df_j_display, f"Laporan Monitoring BPJS - Jenjang {pilih_jenjang_detail}")
                st.download_button("Unduh PDF", data=pdf_j, file_name=f"rekap_{pilih_jenjang_detail.lower().replace(' ', '_')}.pdf", mime="application/pdf", key=f"pdf_{pilih_jenjang_detail}")
                
            st.markdown("---")
            st.markdown(f"##### Hapus Data Sekolah ({pilih_jenjang_detail})")
            opsi_j_sekolah = {f"{row['nama_sekolah']} - ID: {row['id']}": row['id'] for _, row in df_j_terpilih.iterrows()}
            
            if opsi_j_sekolah:
                pilih_hapus_j = st.selectbox("Pilih sekolah yang ingin dihapus:", list(opsi_j_sekolah.keys()), key=f"del_sel_{pilih_jenjang_detail}")
                if st.button("Hapus Data Ini", type="secondary", key=f"btn_del_{pilih_jenjang_detail}"):
                    target_id_j = opsi_j_sekolah[pilih_hapus_j]
                    data_hapus_j = supabase.table("tabel_detail_sekolah").select("*").eq("id", target_id_j).execute()
                    
                    if data_hapus_j.data:
                        item_j = data_hapus_j.data[0]
                        j_nama_jenjang = item_j.get("jenjang")
                        j_sudah_val = item_j.get("jumlah_sudah", 0) or 0
                        
                        supabase.table("tabel_detail_sekolah").delete().eq("id", target_id_j).execute()
                        
                        if j_sudah_val > 0 and j_nama_jenjang:
                            res_rekap_j = supabase.table("tabel_rekap_pendidikan").select("sudah_terdaftar").eq("jenjang", j_nama_jenjang).execute()
                            if res_rekap_j.data:
                                curr_val_j = res_rekap_j.data[0].get("sudah_terdaftar", 0) or 0
                                new_val_j = max(0, curr_val_j - j_sudah_val)
                                supabase.table("tabel_rekap_pendidikan").update({"sudah_terdaftar": new_val_j}).eq("jenjang", j_nama_jenjang).execute()
                                
                        st.success("Data berhasil dihapus dan rekapitulasi diperbarui!")
                        st.rerun()
        else:
            st.info(f"Belum ada data sekolah terdaftar untuk jenjang {pilih_jenjang_detail}.")
    except Exception as e:
        st.error(f"Gagal memuat rincian jenjang: {e}")

with tab4:
    st.subheader("Grafik Persentase Kepesertaan per Jenjang Pendidikan")
    try:
        res_chart = supabase.table("tabel_rekap_pendidikan").select("jenjang, jumlah_ptk, sudah_terdaftar").order("id", desc=False).execute()
        df_chart = pd.DataFrame(res_chart.data)
        
        if not df_chart.empty:
            df_chart["Persentase (%)"] = (df_chart["sudah_terdaftar"] / df_chart["jumlah_ptk"].replace(0, 1)) * 100
            df_chart["Persentase (%)"] = df_chart["Persentase (%)"].round(2)
            
            df_plot = df_chart.set_index("jenjang")[["Persentase (%)"]]
            st.bar_chart(df_plot)
            
            st.markdown("---")
            st.markdown("##### Detail Data Grafik")
            st.dataframe(df_chart, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data untuk ditampilkan dalam grafik.")
    except Exception as e:
        st.error(f"Gagal memuat grafik: {e}")
