# Product Requirement Document (PRD)

**Projeto:** Tachyone SLM — *Beyond the Speed of Light*

**Versão:** 2.0.0

**Data:** 04 de Outubro de 2026

**Status:** Pronto para aprovação *(v2.0.0: escopo clarificado — produto = SLM + shim de serving neste repo; Fase 0 concluída em 03/10 e Fase 1 em 04/10)*

**Repositório do produto (código, dados, docs):** [`munod/tachyone_slm`](https://github.com/munod/tachyone_slm) @ `f6a4218` (main, out/2026)

**Repositório de referência (somente leitura — `WS-AD-010`):** [`munod/tachyone`](https://github.com/munod/tachyone) @ `164ed3bf` — fornecedor do **contrato** (`/v1/systemone`), do **pipeline de dados** (`training/generate_data.py`), do **harness** (`benchmarks/compare.py`) e do **handoff** (`tachyone.handoff`). **Nenhuma mudança é feita lá.**

**Core Motto:** *"Além da velocidade da luz!"*

---

**Changelog da versão (v1.2 → v2.0) — escopo clarificado:**

* **Produto = SLM + shim de serving, neste repositório.** O SLM é treinado para ser **uma opção de backend `llm` do tachyone**: ativado por configuração (`TACHYONE_BACKEND=llm` + `TACHYONE_LLM_BASE_URL`/`TACHYONE_LLM_MODEL`), sem nenhuma linha no upstream — §1.1, §5.2.
* **`munod/tachyone` vira dependência somente-leitura permanente (`WS-AD-010`).** É referência de contrato, estrutura de dados e régua de avaliação — nunca alvo de escrita. Isso também mantém a submissão JevBench `#182` intocada (`WS-B-022`) — §1.4, §10.
* **§5.2 reescrito:** as superfícies "export no SDK `tachyone.system_two`", "flag no CLI" e "cookbook do upstream migrado" **saem de escopo** — entregamos nossa própria cookbook/examples aqui.
* **§6 Fase 4 reescrita:** integração vira **shim de serving** (nosso servidor expõe API OpenAI-compatível e **monta o `answers` a partir dos logits** — scoring do §3.4 acontece dentro dele) + calibração + política τ/retry/fallback.
* **§6 Fase 5 reescrita:** avaliação roda com o harness **importado em modo leitura** (como na Fase 0); publicação = pesos + model card no HF.
* **§7.6:** "ADR-0017 publicado" substituído por **"decisão de stack registrada (`DEC-002`, local)"** — sem ADR no upstream porque não há código lá.
* **§3.4 mantido e localizado:** a regra de ouro continua (*probabilidade vem dos logits, nunca de texto gerado*), agora explicitada como responsabilidade **do shim**.

---

**Changelog da versão (v1.1 → v1.2) — Fase 0 executada:**

* **Alvos do slice abstido fixados (§2):** `≥ 0,723` (ornith-9b) **e** `≥ 0,474` (System-1), ancorados em **`eval_multi_domains`, n=264** — substituem *"a medir (Fase 0)"*. Medidos no harness `benchmarks/compare.py`, RTX 3060, 2026-10-03 (`docs/phase0-baseline.md`).
* **Denominadores registrados (§2):** `eval_multi` n=18 (secundário) · `eval_en`/`eval_en_domains` n=1/4 — **sem denominador utilizável**, sinalizados conforme o edge case da spec `baseline-system2`.
* **Contexto decidido (§3.1): 2.048 tokens** — A/B idêntico nos dois braços (acurácia 0,212 = 0,212 · `JSON ok` 0,958 = 0,958 · p50 276,2 vs 276,3 ms) porque **0 linhas estouram 2.048 tokens** (máx. 1.360 wire+system).
* **Baselines medidos (§2):** `JSON ok` 0,947 (ornith) · 0,561 (ling) · **0,466 (SLM base)**; VRAM do SLM base **718 MiB**; latência p50 do SLM base 276–554 ms sem SFT.
* **Achado de risco (§8):** o SLM base sem SFT marca **0,098** no mesmo slice — é a lacuna que Fases 1–2 precisam fechar; o modo *scoring* (§3.4) fecha o `JSON ok` por construção.
* **Desvios de protocolo documentados** (cap `-n 1024`, Ollama sem cap, val split 192 linhas, adapters fitted-bank não distribuídos) em `docs/phase0-baseline.md` §5.

---

**Changelog da versão (v1.0 → v1.1):**

* **Papel reenquadrado:** o SLM deixa de ser "o motor autoregressivo oficial" genérico e passa a ser o **System-2 local** do híbrido, invocado pelo handoff de confiança (B-3) — §1.
* **Baselines re-derivados:** todos os números da v1.0 que não reproduzem nas tabelas publicadas do repositório (13,79 ms / 32 req/s / 78,16% `pt` / ECE 0,0589) foram substituídos pelas medições atuais de `docs/compare.md` e `benchmarks/report.md` — §2.
* **Interface alinhada ao wire congelado (ADR-0001):** o prompt de texto livre e o JSON próprio da v1.0 são removidos; request/response passam a seguir `docs/protocol.md` — §5.
* **Dados:** `Tachyone-SML-Dataset-v1` é substituído pela mixture gerada pelo pipeline existente `training/generate_data.py` — §3.3.
* **Hardware corrigido:** FP8 declarado apenas para Ada (NVIDIA L4); RTX 3060 usa bf16/INT8/INT4 — §4.
* **Critérios de aceitação** reescritos e alinhados 1:1 com os KPIs; processo do repositório (ADR, gates, `AGENTS.md`) incorporado — §6–§9.

---

## 1. Visão Geral do Produto

### 1.1 Objetivo

Entregar o **System-2 local** do híbrido Tachyone System-1/System-2: um SLM baseado em **Qwen2.5-0.5B-Instruct** com *Supervised Fine-Tuning* (SFT) via **LoRA**, invocado pelo mecanismo de handoff do B-3 (`assess_response(τ)` → `system_two()`) nos inputs em que o encoder (System-1) **abstém**.

O SLM substitui os candidatos atuais a System-2 medidos no repositório — LLMs locais Q4 servidos via `llama-server` (`ling-tiny`/`ornith-9b`, **1,2–6,8 s p50**, `JSON ok` ≤ 0,889) — por um motor **local, com contrato garantido, calibração fittada e p50 < 20 ms**.

O System-1 (encoder ModernBERT/mmBERT + LoRA) **permanece intocado**; o wire `/v1/systemone` **não muda** (ADR-0001).

**Escopo do produto (v2.0).** O entregável é o **SLM treinado + o shim de serving**, tudo neste repositório (`munod/tachyone_slm`): pesos publicados no HF (`munod/tachyone_slm`), servidor que expõe **API OpenAI-compatível** e **monta o `answers` a partir dos logits** (o scoring do §3.4 acontece *dentro* dele — o modelo nunca escreve os números), e os docs/model card. O SLM é **selecionado por configuração** no backend `llm` já existente do tachyone — nenhuma linha é escrita no upstream, que é **dependência somente-leitura** (§1.4, decisão `WS-AD-010`).

### 1.2 Papel no híbrido System-1 / System-2

```
request ──► System-1 (encoder, ~3,8–6,8 ms p50)
                │
                ▼
        assess_response(τ)  ◄── tachyone.handoff (B-3)
           │            │
     confiança ≥ τ   confiança < τ (abstém)
           │            │
        resposta     system_two()  ◄── stub do usuário lá; aqui: SLM setado
                                   como backend llm por config (§5.2)
                        │
                        ▼
                   SLM local (este PRD) ──► resposta wire válida
                        │ (falha após 1 retry)
                        ▼
                   cadeia de fallback (§5.3)
```

### 1.3 Justificativa (evidências do próprio repositório)

1. **O System-1 não raciocina.** No JevBench público, o encoder está em **Intelligence 15,0** (alvo ≥ 50) e no **nível de chance no hard tier**; duas causas estruturais registradas: o `noul` ignora o rubric (`cos(question, state)` apenas → adequacy no chance) e a inferência trunca em 512 tokens enquanto os estados hard médios têm **1.079 tokens** (máx. 3.746) — BACKLOG B-13/P0. A lição **L-014** mostra que mais contexto não salva o *encoder* de similaridade — mas ler o texto inteiro com um modelo autoregressivo é exatamente a hipótese que este SLM testa (Fase 0/4).
2. **Os candidatos a System-2 são bons em qualidade e ruins em velocidade.** `ornith-9b` responde com acurácia **0,611/0,771** nos dois sets de `docs/compare.md` — mas a **3,3–6,8 s p50**, com `ling-tiny` ainda falhando o contrato (`JSON ok` **0,889/0,917** pós-B-10) e ambos usando **4,8–5,5 GB de VRAM**. Um SLM de 0,5B ataca os três defeitos ao mesmo tempo.
3. **O slot System-2 existe e está vazio.** O `cookbook-handoff.md` descreve `system_two()` como stub do usuário ("a frontier LLM, a human reviewer, or a longer pipeline"). Este PRD especifica o **SLM que ocupa esse slot** — servido como opção de backend `llm` por configuração (§5.2).
4. **Por que a confiança não pode ser texto gerado.** `docs/compare.md` §1 registra a crítica central contra LLMs: *"a confidence that was never fitted to anything"*. O SLM herda `calibration.py` (temperature scaling por (primitivo, idioma)) — §3.5.

### 1.4 Não-escopo

* **Não** modifica **nada** em `munod/tachyone` — o upstream é **dependência somente-leitura permanente** (contrato, pipeline de dados, harness e handoff são referência, nunca alvo de escrita) — decisão `WS-AD-010`. Isso mantém preservada, de quebra, a submissão JevBench `#182` (`WS-B-022`).
* **Não** muda o wire `/v1/systemone` (ADR-0001; `tests/test_contract_wire.py` permanece verde sem alteração).
* **Não** substitui nem modifica o backend encoder (System-1).
* **Não** submete o JevBench com o SLM (a submissão segue sendo o artefato do encoder; composição System-1+2 é futuro).
* **Não** treina modelos ≥ 1B nem explore MoE de adapters.
* **Não** envolve serving multi-tenant/nuvem — alvo é o ambiente local-first do projeto.

---

## 2. Objetivos e Métricas Chave (KPIs)

Todas as medições seguem o protocolo do `benchmarks/compare.py`: **sequencial, batch=1, warm-up excluído, mesma linha de dados, mesma implementação de métrica, GPU declarada ao lado do número**.

| Métrica | Meta (v2.0) | Baseline System-2 medido (fonte) |
| --- | --- | --- |
| **Latência p50 in-engine** | **< 20 ms** (stretch: < 8 ms — pré-condições em §4) | 3.315–6.844 ms (`ornith-9b`) · 1.219–1.662 ms (`ling-tiny`) — `docs/compare.md` §3 · SLM base **276 ms** (llama-server) / 554 ms (Ollama) **sem SFT** — Fase 0 |
| **Latência p95 in-engine** | **< 50 ms** | 8,6–50,3 s (dominado por falhas de contrato) · SLM base 1,2 s sem SFT — Fase 0 |
| **Velocidade relativa** | **≥ 50×** o p50 de `ornith-9b` no mesmo harness | referência: 3.315 ms (home) / 6.844 ms (probe) · 6.737 ms no slice abstido — Fase 0 |
| **Throughput no caminho System-2** | **≥ 20 itens/s** (batch=1) | 0,1–0,2 itens/s (`docs/compare.md`) |
| **Contract compliance (`JSON ok`)** | **1,000** nos dois sets | 0,889 / 0,917 (`ling-tiny` pós-B-10) · **Fase 0 no slice:** 0,947 (`ornith-9b`) · 0,561 (`ling-tiny`) · **0,466 (SLM base)** |
| **Acurácia no slice abstido** (τ = 0,6) | **≥ 0,723** (candidato LLM System-2) **e ≥ 0,474** (System-1 no mesmo slice) — âncora **`eval_multi_domains`, n=264**; `eval_multi` (n=18) secundário; `eval_en`/`eval_en_domains` (n=1/4) **sem denominador utilizável** | **Fase 0 (2026-10-03, RTX 3060):** 0,723 (`ornith-9b`) · 0,474 (System-1) · 0,311 (`ling-tiny`) · 0,098 (SLM base) — `docs/phase0-baseline.md` §2 |
| **Acurácia composta** (System-1 + handoff) | ≥ System-1-only (sem regressão) | System-1 hoje: `eval_en` **1,000** · `eval_multi` **0,895** · five-domain **0,9975** — `benchmarks/report.md` (yardstick registrado na Fase 0) |
| **ECE (10-bin, temperature fitted)** | **≤ 0,030** — com **Brier e `Conf` publicados ao lado** (regra L-015) | LLMs: ECE raw 0,10–0,24 · Brier 0,49–0,74 |
| **VRAM adicional do System-2** | **≤ 1,6 GB** (bf16) · **≤ 1,0 GB** (INT4/FP8) | LLMs: 4,8–5,5 GB (`docs/compare.md`) · **SLM base: 718 MiB medido** (Fase 0, 622 MB de pesos em GPU) |
| **Cobertura do handoff** | **100%** dos itens abstidos recebem wire válido (1 retry máx.) | hoje: stub decidido pelo usuário |

**KPIs removidos da v1.0 e por quê:**

* *Latência p50 < 10 ms HTTP E2E / baseline 13,79 ms*: baseline não reproduz em nenhuma tabela publicada atual; papeis trocados (System-2 compete com segundos, não com milissegundos).
* *Throughput > 120 req/s*: requisito de System-1 — o encoder já cobre (24,4 itens/s em `compare.md` home, fast-path 3,83 ms p50).
* *Acurácia Global > 94%, `pt` > 92%*: **já atingido pelo encoder publicado** (`pt` 0,944 em `eval_multi`; five-domain 0,995) — ver `benchmarks/report.md`.
* *ECE < 0,030 como superação do 0,0589*: o 0,0589 não reproduz; o KPI de ECE permanece, agora como requisito do SLM.
* *VRAM < 1,2 GB*: relaxado e redefinido (medido no harness, adicional ao System-1) — 1,2 GB não fecha com pesos bf16 de ~1,0 GB + contexto CUDA.

---

## 3. Arquitetura do Modelo e Fine-Tuning

### 3.1 Base Model

* **Modelo Base:** `Qwen/Qwen2.5-0.5B-Instruct` (~490M parâmetros, vocabulário 151.643, janela nativa 32.768).
* **Contexto de serviço: 2.048 tokens — *decidido na Fase 0* (A/B 2.048 vs 4.096).** Os dois braços foram idênticos no slice abstido (acurácia 0,212 = 0,212 · `JSON ok` 0,958 = 0,958 · p50 276,2 vs 276,3 ms) porque **nenhuma linha dos quatro eval sets passa de 2.048 tokens** — máximo medido 1.360 tokens com o system prompt (`docs/phase0-baseline.md` §3); 4.096 não compra cobertura e só gasta KV-cache. O truncamento de 512 da v1.0 permanece **removido**: ele reproduziria a fraqueza registrada em B-13/P0 (estados hard médios 1.079 tok).
* **KV-cache:** pré-alocado, fixo ao contexto de serviço (≈ 6 MB por 512 tok com GQA — irrelevante frente aos pesos).

### 3.2 Tática de Treino (LoRA / SFT)

* **Método:** LoRA em `bfloat16`, módulos `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj`.
* **Hiperparâmetros:** `r = 16`, `α = 32`, dropout `0,05`, LR `2e-4` com Cosine Decay, batch 32 (gradient accumulation, **effective batch declarado**), **AdamW** (8-bit/bitsandbytes opcional se a 3060 apertar), 3–5 épocas com **early stopping** em `eval_en` + slice abstido.
* **Disciplina de experimento (obrigatória, lições do repo):**
  * seed pinado (**AD-009**) e config idêntica à de lançamento verificada antes de rodar (**L-011**);
  * **control antes de culpar variância** (**L-006**) — a não-determinismo do loop já produziu 0,76–0,79 no mesmo seed;
  * gating sempre no **pior** domínio/idioma, nunca na média;
  * nunca gate em harness *routed* (**L-013**) — adapter explícito nos evals.

### 3.3 Dataset (`Tachyone-SLM-Mixture-v1`)

Gerado pelo **pipeline existente** (`training/generate_data.py`) — não um dataset paralelo:

* **Config nova** `training/configs/data_sft_slm.json`: `--languages en,pt,es,fr,de,it,nl` (os 7 idiomas de treino do repo), `--domains support,ecommerce,agent_tools,documents,voice`, volume ≈ **50.000 registros**, seed pinado.
* **Labels derivadas do texto (ADR-0014/ADR-0015 são lei):** `noul` pela phrase bank, `score` pelo tom, `choice` pela opção que o estado nomeia — repetir o bug de label indexado (B-11/B-12) custou 3 retrains no histórico.
* **Garantias do pipeline:** RNG por registro, saída byte-idempotente (teste de golden-hash), split train/val determinístico.
* **Contaminação:** os eval sets (`eval_en`, `eval_multi`, `eval_en_domains`, `eval_multi_domains`, probes públicos) **nunca** aparecem nos prompts do gerador nem no val de temperature fit; auditoria de overlap registrada.
* **Renderização SFT:** cada registro vira *(prompt = request do wire renderizado)* → *(alvo conforme a estratégia de §3.4)*, com a grammar/filtro de validação do §5.4 aplicado na geração dos pares.

### 3.4 Estratégia de Decodificação e Confiança *(decisão registrada)*

**Decisão padrão: *scoring de candidatos* (não geração livre) para montar a resposta.**

* `choice`: logprob comprimento-normalizado de cada rótulo de `criteria` como continuação do mesmo prefixo (batch com prefixo compartilhado) → `probabilities = softmax(logprobs)` (**soma 1,0 por construção**), `confidence` = massa do rótulo modal.
* `noul`: `noul = sigmoid(ℓ(true) − ℓ(false))` com os textos de `criteria.true/false` → **float 0..1** (o wire não tem `ptrue` nem string `"false"`).
* `score`: softmax sobre os rótulos de nível → `probabilities` por índice, `score = Σ i·pᵢ` (valor esperado, como o exemplo do `protocol.md`), `legend` montada do request, `confidence` = massa do índice modal.

**Por quê:** compliance por construção (não existe texto livre fora do schema), distribuições nativas (invariante do wire), custo estável mesmo com as **255 options** permitidas pelo contrato — B-10 mediu **46 s por tentativa de 52 options** em geração livre — e coerência com a identidade "single forward pass" do projeto (mesma classe de solução do peer `pngwn/system-one-qwen3.5-4b-scorer`).

**Onde roda (v2.0):** o scoring acontece **dentro do shim de serving** (§5.2) — exposto como API OpenAI-compatível. O cliente upstream (`TACHYONE_BACKEND=llm`) faz `chat/completions`, o shim pontua os rótulos nos logits e **devolve o objeto `answers` montado pelo runtime**; o upstream apenas parseia esse JSON. Nenhuma linha muda em `munod/tachyone`.

**Alternativa documentada (modo experimental, Fase 4):** *geração com constrained decoding* dos **valores** do wrapper `answers` (≈ 4–8 tokens/registro; o runtime monta o JSON final). Único modo que pode emitir raciocínio interno (scratchpad anterior ao wrapper, descartado pelo runtime) — candidato natural para o slice hard. Riscos: compliance depende da grammar, `probabilities` exigem rescoring posterior, degrada com muitas opções.

**Regra de ouro:** `confidence`/`probabilities` **nunca são texto gerado pelo modelo** — vêm dos logits e do fit de §3.5.

### 3.5 Calibração

* Temperature scaling com `training/fit_calibration.py`, **por (primitivo, idioma)**, grid 0,25–20,00 (passo 0,05), fit no val do split de treino — nunca nos eval sets.
* Report publica **ECE (10-bin) + Brier + `Conf`** juntos (L-015/L-007: ECE sozinho não é métrica de qualidade).
* Fallback de ativo de calibração: seguir o padrão B-8 — asset ilegível **avisa pelo nome**, nunca degrada em silêncio.

---

## 4. Otimização de Performance: *"Beyond Light Speed"*

1. **Fusão e exportação:** merge dos pesos LoRA no trunk → export para **vLLM** (FP8) ou **TensorRT-LLM**. Decisão de stack registrada em `DEC-002` (**neste** repositório).
2. **Matriz de hardware (correção da v1.0):**

   | Papel | GPU | Precisão |
   | --- | --- | --- |
   | Treino LoRA | RTX 3060 12GB ou NVIDIA L4 23GB | bf16 |
   | Serving/benchmark (path principal) | RTX 3060 (Ampere, **sem FP8**) | bf16 ou INT4 (AWQ/GPTQ) |
   | Serving/benchmark (stretch < 8 ms) | NVIDIA L4 (Ada/SM89, **FP8 nativo**) | FP8 |

3. **Prefix caching do template fixo** (`system`/`task`/`questions` compartilhados entre requests) — maior alavanca de latência por linha de config; nos engines de serving é flag, não código.
4. **CUDA Graphs + warm-up por shapes:** para o SLM, reusar a captura nativa do vLLM/TRT-LLM (a seam `fast.py` do repo é do encoder). Shapes do warm-up cobrindo o contexto de serviço.
5. **Saída mínula:** no modo padrão (§3.4) o custo de decode é ~0 tokens gerados; no modo experimental de geração, JSON de valores com assembly no runtime (é o que torna o **stretch < 8 ms** plausível: ~5 tokens × ~1 ms/token em FP8/L4 + prefill com prefix caching).
6. **Speculative decoding:** experimento opcional, **não é pré-requisito** — com saída de 4–8 tokens o ganho é marginal; registrar medida antes de mantê-lo.

---

## 5. Requisitos Funcionais e Interface

### 5.1 Interface = wire congelado (`docs/protocol.md`, ADR-0001)

O prompt de texto livre e o JSON próprios da v1.0 **foram removidos** — violavam o contrato (e o B-10 mediu exatamente essa falha em LLMs pequenos). O SLM consome e produz o formato real:

**Input (request canônico):**

```json
{
  "state": "O nosso servidor principal foi abaixo após a última atualização. Precisamos de ajuda imediata!",
  "model": "tachyone-latest",
  "questions": {
    "department": { "type": "choice", "instructions": "Setor responsável.",
                    "criteria": { "billing": null, "technical": null, "sales": null, "other": null } },
    "urgency":    { "type": "score",  "instructions": "Urgência do chamado.",
                    "criteria": ["not urgent", "soon", "blocking"] },
    "churn_risk": { "type": "noul",   "instructions": "Risco de cancelamento?",
                    "criteria": { "true": "ameaça explícita de sair", "false": "sem sinais de saída" } }
  }
}
```

**Output (resposta canônica):**

```json
{
  "model": "tachyone-latest",
  "answers": {
    "department": { "type": "choice", "choice": "technical",
                    "probabilities": { "billing": 0.01, "technical": 0.97, "sales": 0.01, "other": 0.01 },
                    "confidence": 0.97 },
    "urgency":    { "type": "score", "score": 2.03,
                    "legend": { "0": "not urgent", "1": "soon", "2": "blocking" },
                    "probabilities": { "0": 0.01, "1": 0.06, "2": 0.93 }, "confidence": 0.93 },
    "churn_risk": { "type": "noul", "noul": 0.02 }
  },
  "usage": { "input_tokens": 214, "output_tokens": 0 }
}
```

Invariantes obrigatórias: wrapper `answers` presente; `probabilities` com as chaves exatas das opções/índices somando 1,0; `noul` float 0..1; `legend` espelhando o `criteria` do score; `answers` ↔ `questions` na mesma chave.

### 5.2 Integração: SLM como opção de backend `llm` — configuração, não código

* **Ativação = configuração:** o shim expõe API **OpenAI-compatível** e é selecionado pelas env vars que o upstream **já** entende: `TACHYONE_BACKEND=llm`, `TACHYONE_LLM_BASE_URL=<shim>`, `TACHYONE_LLM_MODEL=tachyone-slm`. **Zero código novo em `munod/tachyone`** (`WS-AD-010`).
* **Shim = onde o §3.4 vive:** recebe o `chat/completions`, executa o *scoring* nos logits e devolve o objeto `answers` **montado pelo runtime** — o modelo nunca escreve números, então `JSON ok` é **por construção** e a regra de ouro (§3.4) vale. O payload é validado contra `tachyone.wire` (importado em modo leitura).
* **Plug-in client-side (opcional):** quem quiser compor sem HTTP usa nosso `system_two()` como **biblioteca**, consumindo o `HandoffReport` de `tachyone.handoff`. A cookbook é **a nossa** — a do upstream permanece como stub, sem export no SDK/CLI deles (superfícies que a v1.2 prometia e a v2.0 **remove do escopo**).
* **Modo de execução:** motor local embarcado (transformers/peft) atrás do shim; servidores externos (vLLM/TRT-LLM) como opcional — medir ambos na Fase 5.

### 5.3 Política de τ, retry e cadeia de fallback

* **τ configurável, sem default universal** (tabela do cookbook: ≈0,3 segurança · ≈0,5 roteamento · ≈0,8 automação); τ de referência do benchmark: **0,6**.
* **Retry:** 1 tentativa por item abstido; falha de parse/construção **não** é silenciosamente aceita.
* **Cadeia documentada:** SLM local → LLM remoto (`llm` backend) → revisão humana, com a cadeia explícita na resposta de diagnóstico (objeto `handoff` já existe no CLI). O "Zero Fallbacks" da v1.0 vira: **`JSON ok` = 1,000 (§7.1) + cadeia de falha documentada**.

### 5.4 Constrained decoding / schema

* A grammar/JSON Schema **do contrato** é a fonte do constrained decoding (XGrammar/llguidance ou `guided_json` do vLLM) no modo experimental de geração; no modo padrão (§3.4) a validade é por construção e o schema atua como verificação final.
* Schema publicado **neste repositório** (anexo de `DEC-002`) e validado contra o contrato do upstream — `tests/test_contract_wire.py` é executado em modo leitura, **nunca editado**.

---

## 6. Plano de Execução e Cronograma

```
[Fase 0: Baseline System-2] ► [Fase 1: Dados] ► [Fase 2: SFT/LoRA] ► [Fase 3: Export] ► [Fase 4: Integração] ► [Fase 5: Benchmark & Docs]
       (Dia 1)                 (Dias 2–3)          (Dias 4–5)          (Dia 6)            (Dias 7–8)               (Dias 9–10)
```

* **Fase 0 — Baseline do slice abstido (1 dia) — ✅ CONCLUÍDA (2026-10-03):** System-1 + candidatos LLM medidos no slice `confidence < τ=0,6` dos eval sets; **alvos da §2 fixados**; A/B de contexto decidido (2.048). Saída: `docs/phase0-baseline.md` + artefatos `benchmarks/results/phase0_*.json`.
* **Fase 1 — Mixture SFT (1–2 dias):** config `data_sft_slm.json`, ~50k registros, golden-hash, auditoria de contaminação, renderizador prompt/alvo do §3.4.
* **Fase 2 — Treino LoRA/SLM (2 dias):** **decisão de stack registrada em `DEC-002` antes de codar**; os scripts de treino vivem **neste repo**, usando o pipeline upstream (`training/finetune_rlcd.py`, peft) como **referência em modo leitura**; execução com a disciplina da §3.2 (~4–12 h de GPU estimados).
* **Fase 3 — Export e quantização (1 dia):** merge LoRA; export vLLM/TRT-LLM; INT4 para 3060, FP8 para L4; VRAM medida.
* **Fase 4 — Integração (1–2 dias):** **shim de serving** (API OpenAI-compatível que executa o scoring do §3.4 e monta o `answers`), modo de decodificação, fit de calibração, política τ/retry/fallback + **cookbook própria**; **contract suite do upstream intocada** (executada em modo leitura).
* **Fase 5 — Benchmark e publicação (1–2 dias):** harness **importado em modo leitura** (`benchmarks/compare.py` — as 4 rows existentes são a régua; a row do SLM entra no **nosso** relatório); publicação de **pesos + model card no HF**; docs em **inglês** neste repo: `README`, `docs/model-card.md`, `CHANGELOG.md`, cookbook própria, relatório de benchmark local.
* **Gates do repositório (todo dia):** `ruff check` · `ruff format --check` · `pyright` · `pytest` · `mkdocs build --strict` · conventional commits · docs/PRs em inglês (`AGENTS.md`/`CONTRIBUTING.md`).

---

## 7. Critérios de Aceitação

1. **Contract compliance:** `JSON ok` = **1,000** nos dois sets do `benchmarks/compare.py` (evidência do risco: B-10, 0,889 para LLM promptado).
2. **Qualidade no papel de System-2:** cobertura 100% dos itens abstidos; acurácia do slice **≥ 0,723** (candidato LLM `ornith-9b`) **e ≥ 0,474** (System-1) em `eval_multi_domains` (n=264, τ=0,6) — alvos fixados pela Fase 0; acurácia composta ≥ System-1-only (1,000 / 0,895 / 0,9975); **sem regressão** — `eval_en` permanece 1,000 e os golden-hash dos datasets intactos (revalidados: 46/46 na Fase 0).
3. **Latência:** p50 **< 20 ms** e p95 **< 50 ms** in-engine com GPU e método declarados; **≥ 50×** o p50 de `ornith-9b`; **< 8 ms** registrado como *stretch* apenas com as pré-condições da §4 (FP8@L4 + modo de saída mínula).
4. **Calibração:** ECE (10-bin, fitted por primitivo×idioma) **≤ 0,030**, com **Brier e `Conf` publicados ao lado**.
5. **Recursos:** VRAM adicional ≤ **1,6 GB** (bf16) / ≤ **1,0 GB** (INT4/FP8), medida no harness; throughput ≥ **20 itens/s**.
6. **Processo:** **decisão de stack registrada (`DEC-002`, local — sem ADR no upstream, `WS-AD-010`)**; gates verdes (`ruff check` · `ruff format --check` · `pyright` · `pytest` · `mkdocs build --strict`); superfícies documentadas (`CHANGELOG`, cookbook própria, `model-card`, relatório de benchmark) atualizadas **como um conjunto** (padrão AD-009).

---

## 8. Riscos

| Risco | Evidência conhecida | Mitigação |
| --- | --- | --- |
| Variância de treino (o mesmo seed cai em 0,76–0,79) | L-005/L-006 (B-9) | control obrigatório antes de qualquer conclusão; seed pinado |
| O slice abstido não melhora com 0,5B (hard tier é difícil por natureza) | JevBench hard ≈ chance para o encoder; `noul` cego ao rubric; **Fase 0: SLM base sem SFT = 0,098 no slice (n=264)** | alvo fixado **antes** do treino (0,723 / 0,474); se não ganhar, o PRD registra o resultado e reavalia o papel |
| Slice τ=0,6 minúsculo nos eval sets de inglês (n=1 e n=4) — denominador insuficiente para alvo | Fase 0: confiança média do System-1 0,99–0,994; só `eval_multi_domains` tem n=264 | alvo ancorado em `eval_multi_domains`; alternativas registradas (τ maior — sweep 0,3–0,95 no relatório —, eval sets mais difíceis) |
| Contaminação de eval via mixture sintética | L-005 (in-sample synthetic) + regra de eval congelado | auditoria de overlap na Fase 1; probes públicos (B-7) como checagem externa |
| Stretch < 8 ms inatingível | roofline: decode é bandwidth-bound; JSON completo ≈ 60 tok | meta dura é < 20 ms; stretch condicionado a FP8@L4 + saída mínula, medido — não prometido |
| Novas dependências de serving (vLLM/TRT-LLM) vs stack `uv` do repo | extras `serve`/`train`/`fast` já existem como precedente | decisão registrada em `DEC-002` (local); extras opt-in |
| GPU Ada indisponível para o stretch | L4 é a box de treino atual | caminho principal (3060/INT4) não depende de Ada |
| Regressão em inglês por fine-tuning | histórico de retreinos B-11/B-12 | early stopping em `eval_en`; System-1 nunca é re-treinado aqui |

---

## 9. Rastreabilidade (KPI ↔ Seção ↔ Aceitação)

| KPI (§2) | Seção | Critério (§7) |
| --- | --- | --- |
| p50/p95/velocidade/throughput | §4 | 7.3, 7.5 |
| `JSON ok` 1,000 / cobertura do handoff | §3.4, §5.1, §5.3 | 7.1, 7.2 |
| Acurácia slice abstido / composta | §1.2, §3.3, §6 (Fase 0) | 7.2 |
| ECE / Brier / Conf | §3.5 | 7.4 |
| VRAM | §4 | 7.5 |
| Processo e publicação | §6 | 7.6 |

---

## 10. Referências — produto aqui, upstream só como leitura

* **Produto (este PRD):** [`munod/tachyone_slm`](https://github.com/munod/tachyone_slm) (repo) · HF de pesos [`munod/tachyone_slm`](https://huggingface.co/munod/tachyone_slm) · dataset [`munod/tachyone_slm_mixture_v1`](https://huggingface.co/datasets/munod/tachyone_slm_mixture_v1)
* **Referências abaixo (repositório `munod/tachyone`, somente leitura — `WS-AD-010`):**

* Contrato: `docs/protocol.md` · `docs/adr/ADR-0001-jev-drop-in-protocol.md`
* Handoff System-2: `src/tachyone/handoff.py` · `docs/cookbook-handoff.md` (B-3)
* Backend LLM e evidência de compliance: `src/tachyone/backends/llm.py` · `docs/compare.md` §3 (B-10)
* Dados: `training/generate_data.py` · ADR-0014/ADR-0015 · `.specs/project/BACKLOG.md` (B-5, B-11, B-12)
* Calibração: `src/tachyone/calibration.py` · `training/fit_calibration.py` (L-015, B-8)
* Benchmarks: `benchmarks/compare.py` · `benchmarks/report.md` · `benchmarks/probes.md`
* JevBench: `.specs/features/jevbench/spec.md` (B-13, L-014) · `docs/jevbench.md`
* Fast path do encoder (padrão a reusar): `src/tachyone/fast.py` (B-2, ADR-0012)
* Processo: `AGENTS.md` · `CONTRIBUTING.md` · `.specs/project/STATE.md` (L-005…L-016, AD-009)
