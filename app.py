import io
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import pytz # Necessário para o fuso horário

app = FastAPI(
    title="PDF Text Overlay API",
    description="API para adicionar texto na capa."
)

# --- Lógica de Adicionar Texto (Endpoint /process-pdf/) ---

def add_text_to_pdf_logic(pdf_bytes: bytes, nome: str, telefone: str) -> bytes:
    """
    Lógica central para adicionar texto formatado ao PDF como overlay.
    """
    
    # 1. Criar um PDF temporário (overlay) com o texto usando ReportLab
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    # Coordenadas iniciais (começando do topo)
    x_margin = inch
    # --- ALTERAÇÃO DE POSIÇÃO AQUI ---
    y_position = letter[1] - 0.25 * inch # Começa 0.5 polegada do topo (mais para cima)
    # ----------------------------------
    
    # Fuso Horário de São Paulo
    fuso_sp = pytz.timezone('America/Sao_Paulo')
    data_sp = datetime.now(fuso_sp)
    data_atual = data_sp.strftime("%d/%m/%Y")
    
    # --- Conteúdo Formatado ---
    
    # Título Principal (Negrito e Maior)
    can.setFont("Helvetica-Bold", 14)
    can.drawString(x_margin, y_position, "🧬 Instituto Vitalis de Saúde Feminina")
    y_position -= 0.25 * inch
    can.drawString(x_margin, y_position, "Diagnóstico Hormonal Personalizado")
    y_position -= 0.25 * inch
    can.drawString(x_margin, y_position, "Mapa da Cascata Hormonal e Nível de Estresse Endócrino")
    
    y_position -= 0.5 * inch # Espaço
    
    # Informações Dinâmicas (Normal)
    can.setFont("Helvetica", 12)
    can.drawString(x_margin, y_position, f"Nome: {nome}")
    y_position -= 0.2 * inch
    can.drawString(x_margin, y_position, f"Telefone: {telefone}")
    y_position -= 0.2 * inch
    can.drawString(x_margin, y_position, f"Data: {data_atual}")
    y_position -= 0.2 * inch
    can.drawString(x_margin, y_position, "Tipo de Avaliação: Pré-Diagnóstico de Cascata Hormonal")
    
    y_position -= 0.5 * inch # Espaço
    
    # Linha Confidencial (Itálico e Menor)
    can.setFont("Helvetica-Oblique", 10) # Helvetica-Oblique para itálico
    can.drawString(x_margin, y_position, "Relatório confidencial preparado com base nas suas respostas ao questionário de equilíbrio hormonal.")
    
    # --- Fim do Overlay ---
    
    can.save()
    
    # 2. Mesclar o Overlay com o PDF Original
    
    # Mover o ponteiro do BytesIO para o início para leitura
    packet.seek(0)
    new_pdf = PdfReader(packet)
    
    # Ler o PDF original
    existing_pdf = PdfReader(io.BytesIO(pdf_bytes))
    output = PdfWriter()
    
    # Aplicar o overlay na primeira página (capa)
    if not existing_pdf.pages:
        raise ValueError("O PDF original não contém páginas.")
        
    page = existing_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    output.add_page(page)
    
    # Adicionar as páginas restantes
    for i in range(1, len(existing_pdf.pages)):
        output.add_page(existing_pdf.pages[i])
        
    # Salvar o PDF modificado em um buffer de bytes
    output_buffer = io.BytesIO()
    output.write(output_buffer)
    output_buffer.seek(0)
    
    # Retornar o PDF modificado como bytes
    return output_buffer.getvalue()

@app.post("/process-pdf/")
async def process_pdf(
    pdf_file: UploadFile = File(..., description="O arquivo PDF original."),
    nome: str = Form(..., description="O nome do paciente."),
    telefone: str = Form(..., description="O telefone do paciente."),
):
    """
    Recebe um arquivo PDF, nome e telefone, adiciona o cabeçalho formatado na capa do PDF e retorna o arquivo modificado.
    """
    
    # 1. Ler o conteúdo do arquivo PDF
    try:
        pdf_bytes = await pdf_file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler o arquivo PDF: {e}")

    # 2. Processar o PDF
    try:
        modified_pdf_bytes = add_text_to_pdf_logic(pdf_bytes, nome, telefone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Captura o erro e o detalha para o usuário
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar o PDF: {e}")

    # 3. Retornar o PDF modificado como um StreamingResponse
    return StreamingResponse(
        io.BytesIO(modified_pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=modified_{pdf_file.filename}"
        }
    )

# --- Endpoint de Saúde ---

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "PDF Processor API is running"}
