import json
import asyncio
import chainlit as cl
from openai import OpenAI
from info_segugio.config import Config
from info_segugio.prompts import query_writer_istructions, summarizer_instructions, reflection_instructions
from tavily import TavilyClient

# Inizializzazione del client OpenAI con le configurazioni
client = OpenAI(base_url=Config.AI_API_URL, api_key=Config.AI_API_KEY)

# Funzione per interagire con l'AI
def llm(developer_prompt, user_prompt, temperature = 0, response_format = {"type": "json_object"}):

    response = client.chat.completions.create(
        model=Config.MODEL,
        messages=[
            {"role": "system", "content": developer_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        response_format=response_format
    )
    return response.choices[0].message.content

# Genera una query ottimizzata per la ricerca web
def optimize_search_query(research_topic):
    formatted_instructions = query_writer_istructions.format(research_topic = research_topic)
    result = llm (formatted_instructions, "Genera una query per la ricerca web")
    clean_result = result.strip()
    if clean_result.startswith("```json"):
        clean_result = clean_result[7:]
    if clean_result.startswith("```"):
        clean_result = clean_result[3:]
    if clean_result.endswith("```"):
        clean_result = clean_result[:-3]
    obj = json.loads(clean_result.strip())
    print(obj)
    return obj

def _format_content(result):
    return f"""
    Fonte {result['title']}:\n===\n
    URL: {result['url']}\n===\n
    Contenuto più rilevante: {result['content']}\n===\n\n
    """

# Ricerca web 
def web_search(search_query):
    tavily_client = TavilyClient(api_key=Config.TAVILY_API_KEY)
    max_results = 5
    include_raw = False

    response = tavily_client.search(
                query=search_query,
                max_results=max_results,
                include_raw_content=include_raw,
                search_depth="advanced"
    )

    raw_results = response.get("results", [])

    titles = [result['title'] for result in raw_results]
    contents = [_format_content(result) for result in raw_results]

    return {
        "sources_gathered": titles,
        "web_research_results": contents
    }

# Sintetizza i risultati della ricerca in un riassunto coerente
def summarize_sources(web_research_results, research_topic, running_summary=None):
    current_results = "\n\n".join(web_research_results) if isinstance(web_research_results, list) else str(web_research_results)

    if running_summary:
        message = (
            f"Estendi questo riassunto: {running_summary}\n\n"
            f"Con questi nuovi risultati: {current_results}\n\n"
            f"Sul tema: {research_topic}"
        )
    else:
        message = (
            f"Genera un riassunto di questi risultati: {current_results}\n\n"
            f"Sul tema: {research_topic}"
        )

    output_formatter = None # Vogliamo del testo semplice
    return llm(summarizer_instructions, message, 0.2, output_formatter)       

# Analizza il riassunto corrente e genera una domanda di approfondimento
def reflect_on_summary(research_topic, running_summary):
    result = llm(
        reflection_instructions.format(research_topic=research_topic),
        f"Identifica una lacuna e genera una domanda per la prossima ricerca basandoti su: {running_summary}"
    )
    clean_result = result.strip()
    if clean_result.startswith("```json"):
        clean_result = clean_result[7:]
    if clean_result.startswith("```"):
        clean_result = clean_result[3:]
    if clean_result.endswith("```"):
        clean_result = clean_result[:-3]
    return json.loads(clean_result.strip())

@cl.on_message
async def main(message: cl.Message):
    # Fase 1: Generazione della query iniziale
    user_message = message.content
    osq = await asyncio.to_thread(optimize_search_query, user_message)

    # feedback per l'utente
    query, aspect, reason = osq['query'], osq['aspect'], osq['reason']
    
    await cl.Message(
        author="system_assistant", 
        content=f"Query di ricerca ottimizzata:\n {query}.\n Mi sono soffermato su questo aspetto:\n {aspect}.\n Per questo motivo:\n {reason}.\n"
    ).send()

    # Fase 2: Ciclo di ricerca e approfondimento
    running_summary = None
    max_cycles = 4

    while True:
        # Esegui la ricerca web
        results = await asyncio.to_thread(web_search, query)

        titles = "\n".join(results['sources_gathered'])

        # Feedback per l'utente
        await cl.Message(
            author="system_assistant", 
            content=f"Fonti trovate:\n{titles}"
        ).send()

        # Genera o aggiorna il riassunto
        summary = await asyncio.to_thread(summarize_sources, results['web_research_results'], query, running_summary)
        running_summary = summary

        # Feedback per l'utente
        await cl.Message(author="system_assistant", content=f"Riassunto attuale:\n{summary}").send()

        # se abbiamo finito i cicli Esci
        max_cycles -= 1
        if max_cycles <= 0: 
            break

        # Genera la prossima query di approfondimento
        ros = await asyncio.to_thread(reflect_on_summary, query, summary)

        query = ros.get('domanda_approfondimento', f"Dimmi di più su {query}")
        lacuna_conoscenza = ros.get('lacuna_conoscenza', '')

        # Feedback per l'utente
        await cl.Message(
            author="system_assistant", 
            content=f"Prossima ricerca:\n {query}.\n Mi sono soffermato su questo perchè:\n {lacuna_conoscenza}"
        ).send()

    # Fase 3: Invio del risultato finale
    await cl.Message(
        author="segugio_assistant", 
        content=f"Risposta alla tua domanda:\n\n{message.content}\n\nRisposta finale:\n\n{running_summary}"
    ).send()
