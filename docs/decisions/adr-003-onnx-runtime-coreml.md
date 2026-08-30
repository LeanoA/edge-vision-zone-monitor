# ADR-003: Runtime de Inferencia: ONNX Runtime (CoreML / CPU) vs PyTorch Nativo

- **Estatus:** Aceptado
- **Fecha:** 2026-08-29

## Contexto
El modelo base de pose (`yolo11n-pose`) debe ejecutarse con latencia determinista en dispositivos de borde locales (Apple Silicon M1/M2/M3) y permitir una migración transparente hacia nodos industriales con GPU dedicada (NVIDIA GTX 1050 / Jetson).

## Opciones Consideradas

1. **Inferencia PyTorch Nativa (`torch.jit` / Python Runtime):**
   - *Pros:* Integración directa sin fase de exportación previa.
   - *Contras:* Elevado consumo de memoria RAM/VRAM, runtime pesado (~1.5 GB en disco), sin optimizaciones específicas de grafo ni fusión de capas para silicio local.

2. **ONNX Runtime con Negociación de Execution Providers:**
   - *Pros:* Formato abierto e interoperable; en macOS delega en `CoreMLExecutionProvider` (Apple Neural Engine / GPU Apple) con fallback a `CPUExecutionProvider` (ARM NEON con multi-threading). Desacopla la lógica de negocio de la aceleración física.
   - *Contras:* Requiere paso previo de exportación y validación estática de grafos (`imgsz=640`, opset 17).

3. **TensorRT Nativo Directo:**
   - *Pros:* Máximo rendimiento en silicio NVIDIA.
   - *Contras:* Propietario e incompatible con macOS (Apple Silicon). En GPUs Pascal (GTX 1050 - sm_61) requiere cuantización obligatoria a INT8 debido a la penalización de hardware de FP16.

## Decisión Tomada
Se adopta **ONNX Runtime** como motor de ejecución desacoplado con la clase `OnnxEngine`. Para desarrollo y demo local se opera con `CoreMLExecutionProvider` / `CPUExecutionProvider` (4 hilos). Para la posterior etapa de despliegue en NVIDIA GTX 1050, se mantendrá la misma interfaz invocando `CUDAExecutionProvider` o TensorRT cuantizado en INT8.

## Consecuencias
- **Rendimiento Comprobado:** Inferencia verificada a $p_{95} = 20.26\text{ ms}$ (54.55 FPS) en Apple Silicon.
- **Portabilidad:** Se cumple el presupuesto temporal de seguridad ISO 13855 ($t_{\text{infer}} \le 30\text{ ms}$) sin acoplar el código a ningún silicio específico.
