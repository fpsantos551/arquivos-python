import io
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from pypdf import PdfReader, PdfWriter
from pypdf.merger import PdfMerger # <--- CORREÇÃO AQUI
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

app = FastAPI(
    title="PDF Text Overlay & Merge API",
    description="API para adicionar texto na capa e mesclar PDFs usando Python (pypdf e reportlab)."
)

# --- Lógica de Adicionar Texto (Endpoint /process-pdf/) ---

def add_text_to_pdf_logic(pdf_bytes: bytes, text_to_add: str) -> bytes:
    """
    Lógica central para adicionar texto ao PDF.
    """
    # 1. Criar um PDF temporário (overlay) com o texto usando ReportLab
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    # Configurações de texto
    can.setFont("Helvetica-Bold", 36)
    
    # Coordenadas para o topo da página (ajustar conforme necessário)
    x_center = letter[0] / 2
    y_top = letter[1] - 0.75 * inch 
    
    # Centralizar o texto no topo
    can.drawCentredString(x_center, y_top, text_to_add)
    
    can.save()
    
    # Mover o ponteiro do BytesIO para o início para leitura
    packet.seek(0)
    new_pdf = PdfReader(packet)
    
    # 2. Ler o PDF original
    existing_pdf = PdfReader(io.BytesIO(pdf_bytes))
    output = PdfWriter()
    
    # 3. Aplicar o overlay na primeira página (capa)
    if not existing_pdf.pages:
        raise ValueError("O PDF original não contém páginas.")
        
    page = existing_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    output.add_page(page)
    
    # 4. Adicionar as páginas restantes
    for i in range(1, len(existing_pdf.pages)):
        output.add_page(existing_pdf.pages[i])
        
    # 5. Salvar o PDF modificado em um buffer de bytes
    output_buffer = io.BytesIO()
    output.write(output_buffer)
    output_buffer.seek(0)
    
    # 6. Retornar o PDF modificado como bytes
    return output_buffer.getvalue()

@app.post("/process-pdf/")
async def process_pdf(
    pdf_file: UploadFile = File(..., description="O arquivo PDF original."),
    name: str = Form(..., description="O nome a ser escrito na capa do PDF.")
):
    """
    Recebe um arquivo PDF e um nome, adiciona o nome na capa do PDF e retorna o arquivo modificado.
    """
    
    # 1. Ler o conteúdo do arquivo PDF
    try:
        pdf_bytes = await pdf_file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler o arquivo PDF: {e}")

    # 2. Processar o PDF
    try:
        modified_pdf_bytes = add_text_to_pdf_logic(pdf_bytes, name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar o PDF: {e}")

    # 3. Retornar o PDF modificado como um StreamingResponse
    return StreamingResponse(
        io.BytesIO(modified_pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=modified_{pdf_file.filename}"
        }
    )

# --- Novo Endpoint de Mesclagem de PDF (Endpoint /merge-pdfs/) ---

@app.post("/merge-pdfs/")
async def merge_pdfs(
    pdf_file_1: UploadFile = File(..., description="O primeiro arquivo PDF."),
    pdf_file_2: UploadFile = File(..., description="O segundo arquivo PDF."),
):
    """
    Recebe dois arquivos PDF e retorna um único arquivo PDF mesclado.
    """
    
    # 1. Ler o conteúdo dos arquivos PDF
    try:
        pdf_bytes_1 = await pdf_file_1.read()
        pdf_bytes_2 = await pdf_file_2.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler os arquivos PDF: {e}")

    # 2. Mesclar os PDFs
    try:
        merger = PdfMerger()
        
        # Anexar o primeiro PDF
        merger.append(io.BytesIO(pdf_bytes_1))
        
        # Anexar o segundo PDF
        merger.append(io.BytesIO(pdf_bytes_2))
        
        # Salvar o PDF mesclado em um buffer de bytes
        output_buffer = io.BytesIO()
        merger.write(output_buffer)
        output_buffer.seek(0)
        
        modified_pdf_bytes = output_buffer.getvalue()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao mesclar os PDFs: {e}")

    # 3. Retornar o PDF mesclado como um StreamingResponse
    return StreamingResponse(
        io.BytesIO(modified_pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=merged_document.pdf"
        }
    )

# Endpoint de saúde para verificar se a API está funcionando
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "PDF Processor API is running"}
