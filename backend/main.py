from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import uvicorn
import os
import json
from agent import agent_instance as agent
from analyzer import auto_eda, generate_plots, clean_for_json, get_failure_stats, get_correlation_stats
from reporting import get_failures, save_report, list_reports, get_report

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Analysis Cache: Stores pre-computed reports for instant access
# Structure: { "why": "Report Text...", "fix": "Report Text..." }
# Analysis Cache: Stores pre-computed reports for instant access
# Structure: { "why": "Report Text...", "fix": "Report Text..." }
ANALYSIS_CACHE = {}

DATASTORE = {}

# Store for user-defined acronyms
DATASTORE["acronyms"] = {}

import threading
from tools import search_web



def run_background_analysis(df, machine_name):
    """
    Runs key analyses in the background so they are ready when requested.
    """
    print("Background Analysis Started...")
    
    # Initialize placeholders
    ANALYSIS_CACHE['why'] = "Analyzing..."
    ANALYSIS_CACHE['impact'] = "Analyzing..."
    ANALYSIS_CACHE['fix'] = "Analyzing..."
    
    # 1. Root Cause (Why)
    print("Pre-computing Root Cause...")
    try:
        agent.set_df(df, context_data={"machine_name": machine_name})
        
        # Build Statistical Context
        f_stats = get_failure_stats(df)
        c_stats = get_correlation_stats(df)
        
        if "error" in f_stats:
            ANALYSIS_CACHE['why'] = f"Analysis Skipped: {f_stats['error']}"
        elif f_stats["total_failures"] == 0:
            ANALYSIS_CACHE['why'] = "No failures detected. Root cause analysis not required."
        else:
            # Build Knowledge Context (Definitions ONLY)
            knowledge_context = ""
            if f_stats["modes"]:
                knowledge_context += "\nSemantic Definitions:\n"
                for mode in f_stats["modes"]:
                    name = mode['name']
                    definition = None
                    source = None
                    
                    # 1. Manuals
                    rag_hits = kb.search_manuals(f"What does failure mode {name} mean?", k=1)
                    if rag_hits:
                        definition = rag_hits[0]
                        source = "Manuals"
                    
                    # 2. User Acronyms
                    if not definition and name in DATASTORE.get("acronyms", {}):
                        definition = DATASTORE["acronyms"][name]
                        source = "User Definition"
                        
                    # 3. Web Search
                    if not definition:
                        try:
                            web_res = search_web(f"meaning of {name} failure mode reliability engineering")
                            if web_res:
                                definition = web_res[:200]
                                source = "Web Search"
                        except: pass
                            
                    if definition:
                        knowledge_context += f"- **{name}**: {definition} [Source: {source}]\n"
                    else:
                        knowledge_context += f"- **{name}**: No semantic definition available.\n"

            # Construct Combined Prompt (Data + Knowledge)
            prompt_failure = f"""
TASK: Perform a complete Failure Analysis.

DATA CONTEXT:
Dataset summary:
- Total records: {f_stats['total_records']}
- Total failures: {f_stats['total_failures']}

Failure mode breakdown:
"""
            for m in f_stats["modes"]:
                prompt_failure += f"- {m['name']}: {m['count']} ({m['percent']:.1f}%)\n"

            prompt_failure += "\nStatistical observations:\n"
            if f_stats["modes"]:
                prompt_failure += f"- Most frequent: {f_stats['modes'][0]['name']}\n"
            
            prompt_failure += "\nCorrelation insights:\n"
            if "top_correlations" in c_stats and c_stats["top_correlations"]:
                for item in c_stats["top_correlations"]:
                    prompt_failure += f"  {item['feature']}: {item['value']:.2f}\n"

            prompt_failure += knowledge_context

            # RAG for repair (Global search)
            hits = kb.search_manuals("Repair procedures for detected failures", k=3)
            if hits:
                prompt_failure += "\nMANUAL EXCERPTS:\n" + "\n".join(hits)

            # SINGLE CALL
            full_report = agent.generate_direct(prompt_failure, system_type="failure")
            
            # Store in cache (all keys point to valid report to support legacy endpoints)
            ANALYSIS_CACHE['combined'] = full_report
            ANALYSIS_CACHE['why'] = full_report
            ANALYSIS_CACHE['impact'] = full_report
            ANALYSIS_CACHE['fix'] = full_report
            
        print("Failure Analysis Computed (Combined).")
    except Exception as e:
        print(f"Error computing Failure Analysis: {e}")
        ANALYSIS_CACHE['combined'] = f"Analysis Failed: {str(e)}"
    
    print("Background Analysis Complete! Cache populated.")

class Query(BaseModel):
    question: str

class AcronymPayload(BaseModel):
    acronyms: dict

@app.post("/settings/acronyms")
def update_acronyms(payload: AcronymPayload):
    DATASTORE["acronyms"].update(payload.acronyms)
    return {"message": "Acronyms updated", "total": len(DATASTORE["acronyms"])}

@app.get("/settings/acronyms/unknown")
def get_unknown_acronyms():
    df = DATASTORE.get("df")
    if df is None:
        return {"error": "No dataset loaded"}
        
    stats = get_failure_stats(df)
    if "error" in stats:
        return {"unknown": []}
        
    unknown = []
    known = DATASTORE.get("acronyms", {})
    
    for m in stats.get("modes", []):
        name = m["name"]
        # If not known and looks like an acronym (simple heuristic or just pass all modes)
        if name not in known:
            unknown.append(name)
            
    return {"unknown": unknown}

from fastapi import Form
from typing import Optional

@app.post("/upload")
def upload_csv(file: UploadFile = File(...), machine_name: Optional[str] = Form(None)):
    try:
        df = pd.read_csv(file.file)
        # Basic sanitization: strip whitespace from headers
        df.columns = df.columns.str.strip()
        DATASTORE["df"] = df
        DATASTORE["machine_name"] = machine_name # Store the context
        
        # Clear old cache
        ANALYSIS_CACHE.clear()
        
        # Calculate true failures
        stats = get_failure_stats(df)
        if "error" in stats:
             failure_count = df.shape[0] if stats["error"] == "No target column found" else 0
             unknown = []
        else:
             failure_count = stats["total_failures"]
             # Identify unknown acronyms
             known = DATASTORE.get("acronyms", {})
             unknown = []
             for m in stats.get("modes", []):
                 if m["name"] not in known:
                     unknown.append(m["name"])

        # Create status
        if unknown:
            status = "waiting_for_definitions"
            message = "Dataset uploaded. Please define failure modes."
        else:
            status = "analysis_started"
            message = "Dataset uploaded. Analysis starting..."
            # Start Background Analysis Thread immediately if everything is known
            thread = threading.Thread(target=run_background_analysis, args=(df, machine_name))
            thread.daemon = True
            thread.start()

        return {
            "message": message,
            "filename": file.filename,
            "rows": df.shape[0],
            "failure_count": failure_count,
            "columns": df.shape[1],
            "unknown_acronyms": unknown,
            "status": status
        }
    except Exception as e:
        return {"error": f"Failed to parse CSV: {str(e)}"}

@app.post("/analysis/start")
def start_analysis():
    df = DATASTORE.get("df")
    machine_name = DATASTORE.get("machine_name")
    
    if df is None:
        raise HTTPException(status_code=400, detail="No dataset loaded")
        
    # Check if already running? (Optional optimization)
    # We just restart/overwrite the thread. Python threads can't be killed easily, 
    # but run_background_analysis checks cache keys so it might overlap.
    # However, for this single-user local app, it's fine.
    
    thread = threading.Thread(target=run_background_analysis, args=(df, machine_name))
    thread.daemon = True
    thread.start()
    
    return {"message": "Analysis started", "status": "started"}



from analyzer import auto_eda, generate_plots, clean_for_json

@app.get("/eda")
def get_eda():
    df = DATASTORE.get("df")
    if df is None:
        return {"error": "No dataset has been uploaded"}
    return auto_eda(df)

@app.get("/eda_plots")
def get_eda_plots():
    df = DATASTORE.get("df")
    if df is None:
        return {"error": "No dataset has been uploaded"}
    try:
        plots = generate_plots(df)
        return plots
    except Exception as e:
        return {"error": str(e)}

@app.get("/data")
def get_data(page: int = 1, limit: int = 50):
    df = DATASTORE.get("df")
    if df is None:
        return {"error": "No dataset has been uploaded"}
    
    start = (page - 1) * limit
    end = start + limit
    
    # Slice and clean
    subset = df.iloc[start:end]
    data = subset.to_dict(orient="records")
    return {
        "page": page,
        "limit": limit,
        "total_rows": len(df),
        "data": clean_for_json(data)
    }

import time
from fastapi import HTTPException

import os
import shutil
from knowledge import kb

LAST_CHAT_TIME = 0

@app.post("/manuals/upload")
async def upload_manual(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith(".pdf"):
            return {"error": "Only PDF files are supported."}
            
        file_path = os.path.join("backend", "manuals", file.filename)
        
        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Ingest into Knowledge Base (RAG)
        success, message = kb.ingest_manual(file_path)
        
        if success:
            return {"message": f"Manual uploaded and indexed: {message}"}
        else:
            return {"error": f"Upload successful but indexing failed: {message}"}
            
    except Exception as e:
        return {"error": f"Upload failed: {str(e)}"}

@app.get("/manuals")
def list_manuals():
    try:
        manuals_dir = os.path.join("backend", "manuals")
        if not os.path.exists(manuals_dir):
            return []
        return [f for f in os.listdir(manuals_dir) if f.endswith(".pdf")]
    except Exception as e:
        return {"error": str(e)}

@app.post("/chat")
def chat(query: Query):
    global LAST_CHAT_TIME
    current_time = time.time()
    
    # 5-second rate limit
    if current_time - LAST_CHAT_TIME < 5:
        raise HTTPException(
            status_code=429, 
            detail="Rate limit exceeded. Please wait 5 seconds."
        )
    
    LAST_CHAT_TIME = current_time

    df = DATASTORE.get("df")
    if df is None:
        return {"error": "No dataset has been uploaded"}
    
    # Update Agent Environment
    agent.set_df(df, context_data={"machine_name": DATASTORE.get("machine_name")})
    
    # Run Agent Loop
    answer = agent.run(query.question)
    return {"answer": answer}

@app.get("/auto_analysis")
def auto_analysis():
    # ... restored previously ...
    df = DATASTORE.get("df")
    agent.set_df(df, context_data={"machine_name": DATASTORE.get("machine_name")})
    prompt = "Perform a comprehensive reliability analysis..."
    report = agent.run(prompt)
    return {"report": report}

@app.get("/analysis/fast_failure")
def fast_failure_analysis():
    df = DATASTORE.get("df")
    if df is None:
        return {"error": "No data loaded"}
    
    from analyzer import analyze_failure_modes
    report = analyze_failure_modes(df)
    return {"answer": report}

@app.get("/analysis/report")
def get_cached_report(type: str = "why"):
    """
    Returns the pre-computed analysis from the cache.
    Types: 'why' (Root Cause), 'impact' (Impact), 'fix' (Repair)
    """
    if type in ANALYSIS_CACHE:
        answer = ANALYSIS_CACHE[type]
        if answer == "Analyzing...":
             return {"answer": "Background analysis in progress. Please wait...", "status": "pending"}
        elif "Analysis Failed" in answer:
             return {"answer": answer, "status": "error"}
        else:
             return {"answer": answer, "status": "ready"}
    else:
        # Cache missing entirely - means upload never happened or server restarted
        return {"answer": "No analysis data found. Please re-upload CSV.", "status": "error"}

@app.get("/failures")
def get_failure_list():
    df = DATASTORE.get("df")
    if df is None:
        return {"error": "No data loaded"}
    
    failures = get_failures(df)
    return {"failures": failures}

@app.post("/reports/save")
def save_current_report(analysis_type: str = Body(..., embed=True)):
    df = DATASTORE.get("df")
    machine_name = DATASTORE.get("machine_name")
    
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
        
    report_id, msg = save_report(df, machine_name, analysis_type)
    return {"id": report_id, "message": msg}

@app.get("/reports")
def get_all_reports():
    return list_reports()

@app.get("/reports/{report_id}")
def get_single_report(report_id: str):
    data = get_report(report_id)
    if data:
        return data
    raise HTTPException(status_code=404, detail="Report not found")

# --- Settings API ---

@app.get("/settings/config")
def get_settings_config():
    conf = agent.get_config()
    conf["rag_depth"] = kb.n_results
    return conf

@app.get("/settings/models")
def get_settings_models():
    return {"models": agent.get_available_models()}

class ModelUpdate(BaseModel):
    model: str

@app.post("/settings/model")
def update_settings_model(update: ModelUpdate):
    msg = agent.set_model(update.model)
    return {"message": msg, "current_model": agent.model}

class TempUpdate(BaseModel):
    temperature: float

@app.post("/settings/temperature")
def update_settings_temp(update: TempUpdate):
    msg = agent.set_temperature(update.temperature)
    return {"message": msg, "temperature": agent.temperature}

@app.post("/manuals/clear")
def clear_manuals_kb():
    success, msg = kb.clear_index()
    if success:
        return {"message": msg}
    else:
        raise HTTPException(status_code=500, detail=msg)

class ExpertConfig(BaseModel):
    system_prompt: str = None
    ollama_url: str = None

@app.post("/settings/expert")
def update_expert_settings(config: ExpertConfig):
    msg = agent.set_config(config.dict(exclude_none=True))
    return {"message": msg}

class RagUpdate(BaseModel):
    n_results: int

@app.post("/settings/rag")
def update_rag_settings(update: RagUpdate):
    msg = kb.set_depth(update.n_results)
    return {"message": msg, "depth": kb.n_results}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
