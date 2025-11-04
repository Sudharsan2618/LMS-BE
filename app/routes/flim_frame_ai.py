"""
Question and Answering Chatbot.
Retrieves relevant book chunks from Pinecone and generates answers using Google Gen AI.
Strictly uses only book knowledge - returns "not in knowledge" for unrelated questions.
"""

import os
import pinecone
import threading
import requests

from flask import Blueprint, request, jsonify, Response

from app.config.ff_config import (
    PINECONE_API_KEY,
    PINECONE_ENV,
    PINECONE_INDEX,
    EMBEDDING_MODEL,
    GENERATION_MODEL,
    SIMILARITY_THRESHOLD,
    TOP_K,
    SYSTEM_PROMPT,
    validate_config
)

# Import Google Gen AI client for embeddings
# Use google.generativeai (same as ai_route.py) for consistency
USE_VERTEX_AI = False
USE_NEW_API = False
USE_GEMINI_API = False
genai_client = None
embedding_model = None

# Try GEMINI_API_KEY first (same as ai_route.py), then GOOGLE_API_KEY, then fallback
# Note: Don't raise exceptions at import time - allow graceful failure when endpoints are called
try:
    # Check for GEMINI_API_KEY first (same as ai_route.py)
    gemini_api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if gemini_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_api_key)
            genai_client = genai
            USE_GEMINI_API = True
        except Exception as e:
            # Log but don't fail - will be caught when endpoint is called
            print(f"Warning: Failed to initialize google.generativeai: {str(e)}")
            pass
except Exception as e:
    pass

# If USE_GEMINI_API not set, try new Google Gen AI SDK
if not USE_GEMINI_API:
    try:
        if os.environ.get("GOOGLE_API_KEY"):
            from google import genai as google_genai
            genai_client = google_genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
            USE_NEW_API = True
    except Exception:
        pass

# If still not initialized, try Vertex AI (last resort)
if not USE_GEMINI_API and not USE_NEW_API:
    try:
        from vertexai.language_models import TextEmbeddingModel
        model_name = EMBEDDING_MODEL if "textembedding" in EMBEDDING_MODEL.lower() else "textembedding-gecko@001"
        if not model_name.startswith("textembedding-gecko"):
            model_name = "textembedding-gecko@001"
        embedding_model = TextEmbeddingModel.from_pretrained(model_name)
        USE_VERTEX_AI = True
    except Exception:
        # Don't raise - will be handled when endpoints are called
        pass


def init_pinecone():
    """
    Initialize Pinecone connection and get index.
    
    Returns:
        Pinecone Index object
    """
    # Try newer Pinecone SDK (serverless) first, fallback to older version
    try:
        # Newer Pinecone SDK (serverless) - only needs API key
        from pinecone import Pinecone
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX)
    except Exception:
        # Older Pinecone SDK - needs API key and environment
        if not PINECONE_ENV:
            raise ValueError(
                "PINECONE_ENV is required for older Pinecone SDK. "
                "Get it from https://app.pinecone.io/ -> API Keys section. "
                "Or upgrade to newer Pinecone serverless (no environment needed)."
            )
        pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
        index = pinecone.Index(PINECONE_INDEX)
    
    return index


def embed_texts_genai(texts):
    """
    Create embeddings using Google Gen AI.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors
    """
    vectors = []
    
    if USE_GEMINI_API:
        # Use Google Generative AI REST API for embeddings
        # google.generativeai SDK doesn't support embeddings directly, so we use REST API
        try:
            # Get API key
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise Exception("GEMINI_API_KEY or GOOGLE_API_KEY not found. Please set it in your environment variables.")
            
            # Use embedding model from config, default to text-embedding-004
            embedding_model_name = EMBEDDING_MODEL
            # Map common model names to API format
            if "text-embedding-004" in embedding_model_name.lower():
                embedding_model_name = "text-embedding-004"
            elif "text-embedding-v2" in embedding_model_name.lower():
                embedding_model_name = "text-embedding-v2"
            elif "textembedding-gecko" in embedding_model_name.lower() or "embedding-gecko" in embedding_model_name.lower():
                embedding_model_name = "text-embedding-004"  # Use text-embedding-004 as alternative
            
            # Process each text individually using REST API
            for text in texts:
                try:
                    # Use Google Generative AI REST API for embeddings
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{embedding_model_name}:embedContent?key={api_key}"
                    
                    payload = {
                        "content": {
                            "parts": [{"text": text}]
                        }
                    }
                    
                    response = requests.post(url, json=payload)
                    response.raise_for_status()
                    result = response.json()
                    
                    # Extract embedding vector from response
                    embedding_vector = None
                    if 'embedding' in result:
                        embedding_vector = result['embedding'].get('values')
                    elif 'values' in result:
                        embedding_vector = result['values']
                    
                    # Ensure it's a list/array
                    if embedding_vector is None:
                        raise Exception("No embedding found in API response")
                    
                    # Convert to list if needed
                    if not isinstance(embedding_vector, list):
                        if hasattr(embedding_vector, 'tolist'):
                            embedding_vector = embedding_vector.tolist()
                        elif hasattr(embedding_vector, '__iter__') and not isinstance(embedding_vector, str):
                            embedding_vector = list(embedding_vector)
                        else:
                            raise Exception(f"Embedding is not in list format: {type(embedding_vector)}")
                    
                    # Ensure it's a flat list of numbers
                    if len(embedding_vector) > 0 and isinstance(embedding_vector[0], list):
                        embedding_vector = embedding_vector[0]
                    
                    # Ensure all values are numbers
                    embedding_vector = [float(x) for x in embedding_vector]
                    
                    vectors.append(embedding_vector)
                    
                except requests.exceptions.RequestException as e:
                    raise Exception(f"Failed to create embedding via API: {str(e)}")
                except Exception as e:
                    raise Exception(f"Failed to create embedding for text: {str(e)}")
                    
        except Exception as e:
            raise Exception(
                f"Failed to create embeddings with Google Generative AI: {str(e)}\n"
                f"Make sure GEMINI_API_KEY is set correctly and the embedding model '{embedding_model_name}' is available.\n"
                f"Available models: text-embedding-004, text-embedding-v2"
            )
    
    elif USE_VERTEX_AI:
        # Use Vertex AI Text Embedding Model (recommended)
        try:
            # Vertex AI can handle batch embeddings
            embeddings = embedding_model.get_embeddings(texts)
            vectors = [emb.values for emb in embeddings]
        except Exception as e:
            raise Exception(f"Failed to create embeddings with Vertex AI: {str(e)}")
    
    elif USE_NEW_API:
        # New Google Gen AI SDK (google.genai)
        # Use a valid embedding model name for the new SDK
        embedding_model_name = EMBEDDING_MODEL
        
        # Ensure model name has "models/" prefix if not present
        if not embedding_model_name.startswith("models/"):
            embedding_model_name = f"models/{embedding_model_name}"
        
        # If using old model name format, convert to new format
        if "textembedding-gecko" in embedding_model_name.lower() or "embedding-gecko" in embedding_model_name.lower():
            embedding_model_name = "models/text-embedding-004"  # Default for new SDK
        
        try:
            # Use embed_content directly on the models object with model name
            try:
                # Try batch embedding
                response = genai_client.models.embed_content(
                    model=embedding_model_name,
                    contents=texts
                )
                # Extract embeddings from response
                if hasattr(response, 'embeddings'):
                    vectors = [emb.values if hasattr(emb, 'values') else emb for emb in response.embeddings]
                elif hasattr(response, 'embedding'):
                    # Single embedding - duplicate for batch
                    if hasattr(response.embedding, 'values'):
                        vectors = [response.embedding.values] * len(texts)
                    else:
                        vectors = [response.embedding] * len(texts)
                elif isinstance(response, list):
                    vectors = [item.values if hasattr(item, 'values') else item for item in response]
                elif hasattr(response, 'values'):
                    vectors = [response.values] * len(texts)
                else:
                    vectors = [response]
            except Exception as batch_error:
                # Fallback to individual embeddings
                for text in texts:
                    try:
                        response = genai_client.models.embed_content(
                            model=embedding_model_name,
                            contents=text
                        )
                        if hasattr(response, 'embedding'):
                            if hasattr(response.embedding, 'values'):
                                vectors.append(response.embedding.values)
                            else:
                                vectors.append(response.embedding)
                        elif hasattr(response, 'values'):
                            vectors.append(response.values)
                        elif hasattr(response, 'embeddings') and response.embeddings:
                            vectors.append(response.embeddings[0].values if hasattr(response.embeddings[0], 'values') else response.embeddings[0])
                        else:
                            vectors.append(response)
                    except Exception as e:
                        raise Exception(f"Failed to create embedding for text: {str(e)}")
        except Exception as e:
            raise Exception(
                f"Failed to create embeddings: {str(e)}\n"
                f"Model '{embedding_model_name}' may not be available.\n"
                "Try using: text-embedding-004, embedding-gecko-001, or check available models in Google AI Studio."
            )
    
    else:
        # Fallback: Use Vertex AI if available, otherwise raise error
        try:
            from vertexai.language_models import TextEmbeddingModel
            model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
            embeddings = model.get_embeddings(texts)
            vectors = [emb.values for emb in embeddings]
        except Exception as e:
            raise Exception(
                f"Failed to create embeddings: {str(e)}\n"
                "Please install Vertex AI SDK: pip install google-cloud-aiplatform\n"
                "Or configure Vertex AI credentials. See: https://cloud.google.com/vertex-ai/docs/authentication"
            )
    
    if len(vectors) != len(texts):
        raise Exception(f"Expected {len(texts)} embeddings but got {len(vectors)}")
    
    return vectors


def retrieve_relevant_chunks(index, query_text, top_k=TOP_K):
    """
    Retrieve relevant chunks from Pinecone based on query.
    
    Args:
        index: Pinecone Index object
        query_text: User's question
        top_k: Number of top results to retrieve
        
    Returns:
        List of tuples (metadata, score, text)
    """
    # Get embedding for query
    q_vec = embed_texts_genai([query_text])[0]
    
    # Query Pinecone
    try:
        # Try newer Pinecone SDK format
        res = index.query(
            vector=q_vec,
            top_k=top_k,
            include_metadata=True
        )
        
        # Handle different SDK response formats
        if hasattr(res, 'matches'):
            matches = res.matches
        elif isinstance(res, dict):
            matches = res.get("matches", [])
        else:
            matches = list(res) if hasattr(res, '__iter__') else []
    except Exception as e:
        # Fallback for older SDK
        res = index.query(
            vector=q_vec,
            top_k=top_k,
            include_metadata=True,
            include_values=False
        )
        matches = res.get("matches", []) if isinstance(res, dict) else res.matches
    
    retrieved_chunks = []
    for match in matches:
        # Handle different match formats
        if isinstance(match, dict):
            score = match.get("score", 0.0)
            meta = match.get("metadata", {})
        else:
            score = getattr(match, "score", 0.0)
            meta = getattr(match, "metadata", {})
        
        # Get text from metadata (stored during ingestion)
        text = meta.get("text") if isinstance(meta, dict) else (getattr(meta, "text", None) or "")
        if not text:
            text = meta.get("page_content", "") if isinstance(meta, dict) else ""
        
        retrieved_chunks.append((meta, score, text))
    
    # Sort by score descending (highest first)
    retrieved_chunks.sort(key=lambda x: x[1], reverse=True)
    
    return retrieved_chunks


def generate_answer_strict(question, retrieved_chunks, stream=False):
    """
    Generate answer using only retrieved book chunks.
    Returns "not in knowledge" if question is unrelated.
    
    Args:
        question: User's question
        retrieved_chunks: List of (metadata, score, text) tuples
        stream: If True, yields chunks instead of returning full answer
        
    Returns:
        Answer string (if stream=False) or generator (if stream=True)
    """
    # If no chunks retrieved, return not in knowledge
    if not retrieved_chunks:
        if stream:
            yield "I don't know — that information is not in my knowledge (the books)."
            return
        return "I don't know — that information is not in my knowledge (the books)."
    
    # Check if best match meets similarity threshold
    # Note: Pinecone cosine similarity scores range from 0 to 1, where 1 is most similar
    best_score = retrieved_chunks[0][1] if retrieved_chunks else 0.0
    
    # Debug: print top scores for troubleshooting
    print(f"Debug: Retrieved {len(retrieved_chunks)} chunks, top scores: {[f'{c[1]:.3f}' for c in retrieved_chunks[:3]]}")
    
    if best_score < SIMILARITY_THRESHOLD:
        print(f"Debug: Best score {best_score:.3f} below threshold {SIMILARITY_THRESHOLD}, but proceeding with retrieved chunks anyway")
        # Don't return immediately - let's try with lower threshold
        # Only return if score is really low (< 0.3)
        if best_score < 0.3:
            if stream:
                yield "I don't know — that information is not in my knowledge (the books)."
                return
            return "I don't know — that information is not in my knowledge (the books)."
    
    # Build context from retrieved chunks
    context_parts = []
    for meta, score, text in retrieved_chunks:
        # Extract text - try multiple sources
        if isinstance(meta, dict):
            chunk_text = meta.get("text") or meta.get("page_content") or text
            source = meta.get("source", "Unknown")
            chunk_id = meta.get("chunk_id", "Unknown")
        else:
            chunk_text = text or getattr(meta, "text", None) or getattr(meta, "page_content", "")
            source = getattr(meta, "source", "Unknown")
            chunk_id = getattr(meta, "chunk_id", "Unknown")
        
        # Use text parameter if chunk_text is empty
        if not chunk_text:
            chunk_text = text
        
        if chunk_text:  # Only add if we have text
            context_parts.append(
                f"---\nSource: {source} | {chunk_id} | Similarity Score: {score:.3f}\n\n{chunk_text}\n"
            )
    
    context = "\n".join(context_parts[:TOP_K])
    
    # Build prompt with strict instructions
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Provided documents:\n{context}\n\n"
        f"User question: {question}\n\n"
        'If the answer is not contained in the provided documents, reply exactly: "I don\'t know — that information is not in my knowledge (the books)."'
    )
    
    # Call Gen AI for answer generation
    if USE_NEW_API:
        # New Google Gen AI SDK
        if stream:
            # For streaming, we need to use google.generativeai instead
            try:
                import google.generativeai as genai
                gemini_api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
                if gemini_api_key:
                    genai.configure(api_key=gemini_api_key)
                
                model = genai.GenerativeModel(GENERATION_MODEL)
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=512,
                        temperature=0.0
                    ),
                    stream=True
                )
                
                for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        yield chunk.text
            except Exception as e:
                yield f"\n[Error streaming response: {str(e)}]"
        else:
            # Non-streaming version
            try:
                # Ensure model name has "models/" prefix
                generation_model_name = GENERATION_MODEL
                if not generation_model_name.startswith("models/"):
                    generation_model_name = f"models/{generation_model_name}"
                
                # Use generate_content directly on models
                response = genai_client.models.generate_content(
                    model=generation_model_name,
                    contents=prompt,
                    config={"max_output_tokens": 512, "temperature": 0.0}
                )
                
                # Extract text from response
                if hasattr(response, 'text'):
                    answer_text = response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content'):
                        if hasattr(candidate.content, 'parts'):
                            answer_text = candidate.content.parts[0].text
                        else:
                            answer_text = candidate.content.text if hasattr(candidate.content, 'text') else str(candidate.content)
                    else:
                        answer_text = candidate.text if hasattr(candidate, 'text') else str(candidate)
                elif hasattr(response, 'output'):
                    if hasattr(response.output, 'text'):
                        answer_text = response.output.text
                    elif isinstance(response.output, list) and len(response.output) > 0:
                        answer_text = response.output[0].text if hasattr(response.output[0], 'text') else str(response.output[0])
                    else:
                        answer_text = str(response.output)
                else:
                    answer_text = str(response)
                return answer_text
            except Exception as e:
                raise Exception(f"Failed to generate answer with new API: {str(e)}")
    else:
        # Use google.generativeai (same as ai_route.py)
        try:
            # Check if API key is available
            gemini_api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if not gemini_api_key:
                raise Exception(
                    "GEMINI_API_KEY or GOOGLE_API_KEY not found. Please set it in your environment variables."
                )
            
            import google.generativeai as genai
            genai.configure(api_key=gemini_api_key)
            
            if not hasattr(genai, 'GenerativeModel'):
                raise Exception("google.generativeai SDK not properly configured")
            
            model = genai.GenerativeModel(GENERATION_MODEL)
            
            if stream:
                # Streaming version
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=512,
                        temperature=0.0
                    ),
                    stream=True
                )
                
                for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        yield chunk.text
            else:
                # Non-streaming version
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=512,
                        temperature=0.0
                    )
                )
                return response.text
        except Exception as e:
            if stream:
                yield f"\n[Error streaming response: {str(e)}]"
            else:
                raise Exception(f"Failed to generate answer: {str(e)}")


def is_greeting_or_conversational(question):
    """
    Check if the question is a greeting or conversational question.
    
    Args:
        question: User's question
        
    Returns:
        Tuple (is_greeting_or_conversational: bool, response: str or None)
    """
    question_lower = question.lower().strip()
    
    # Greetings
    greetings = [
        'hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 
        'good evening', 'good night', 'howdy', 'sup', 'what\'s up', 'wassup'
    ]
    
    # Conversational questions
    conversational_patterns = [
        'how can you help', 'what can you do', 'what do you do', 
        'who are you', 'what are you', 'introduce yourself',
        'tell me about yourself', 'how do you work', 'explain yourself',
        'what is your purpose', 'what is your role', 'help me',
        'what help', 'can you help', 'how are you', 'how are things'
    ]
    
    # Check for greetings
    for greeting in greetings:
        if question_lower.startswith(greeting) or question_lower == greeting:
            response = (
                "Hello! I'm your AI assistant for the Learning Management System. "
                "I can help you with questions about course materials, books, and learning content. "
                "Feel free to ask me anything related to your studies!"
            )
            return True, response
    
    # Check for conversational questions
    for pattern in conversational_patterns:
        if pattern in question_lower:
            response = (
                "I'm your AI learning assistant! I can help you by:\n\n"
                "📚 Answering questions about course materials and books in the system\n"
                "💡 Explaining concepts from your learning resources\n"
                "🔍 Finding relevant information from your study materials\n"
                "📖 Providing insights based on the content you're studying\n\n"
                "Just ask me any question related to your courses, and I'll search through the available "
                "materials to give you accurate answers. If the information isn't in the system, I'll let you know."
            )
            return True, response
    
    # Check for thank you messages
    if any(word in question_lower for word in ['thank', 'thanks', 'appreciate']):
        response = (
            "You're welcome! I'm here to help whenever you need assistance with your studies. "
            "Feel free to ask me anything about your course materials!"
        )
        return True, response
    
    # Check for goodbye messages
    if any(word in question_lower for word in ['bye', 'goodbye', 'see you', 'farewell', 'later']):
        response = (
            "Goodbye! Good luck with your studies. Feel free to come back anytime you need help!"
        )
        return True, response
    
    return False, None


def ask_question(question, index=None, stream=False):
    """
    Main function to ask a question and get an answer.
    
    Args:
        question: User's question
        index: Optional Pinecone Index object (will initialize if not provided)
        stream: If True, returns a generator for streaming response
        
    Returns:
        Answer string (if stream=False) or generator (if stream=True)
    """
    # Check if it's a greeting or conversational question
    is_conversational, response = is_greeting_or_conversational(question)
    
    if is_conversational:
        if stream:
            # For streaming, yield the response in chunks for smoother experience
            chunk_size = 20  # Yield approximately 20 characters at a time
            for i in range(0, len(response), chunk_size):
                chunk = response[i:i + chunk_size]
                if chunk:
                    yield chunk
            return
        else:
            return response
    
    # For actual questions, proceed with Pinecone lookup
    if index is None:
        index = init_pinecone()
    
    # Retrieve relevant chunks
    retrieved_chunks = retrieve_relevant_chunks(index, question)
    
    # Generate answer (with or without streaming)
    if stream:
        return generate_answer_strict(question, retrieved_chunks, stream=True)
    else:
        answer = generate_answer_strict(question, retrieved_chunks, stream=False)
        return answer


def interactive_chat():
    """
    Interactive chat loop for asking questions.
    """
    validate_config()
    print("Initializing Pinecone connection...")
    index = init_pinecone()
    print(f"Connected to index: {PINECONE_INDEX}")
    print("\nChatbot ready! Ask questions about the books.")
    print("Type 'quit' or 'exit' to end the conversation.\n")
    
    while True:
        question = input("You: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not question:
            continue
        
        print("\nThinking...")
        try:
            answer = ask_question(question, index)
            print(f"\nBot: {answer}\n")
        except Exception as e:
            print(f"\nError: {str(e)}\n")


if __name__ == "__main__":
    interactive_chat()


# Flask Blueprint for API endpoints
# Create Blueprint
flim_frame_bp = Blueprint('flim_frame', __name__)

# Lazy initialization of Pinecone index (thread-safe)
_pinecone_index = None
_index_lock = threading.Lock()

def get_pinecone_index():
    """Get or initialize Pinecone index (singleton pattern)."""
    global _pinecone_index
    if _pinecone_index is None:
        with _index_lock:
            if _pinecone_index is None:
                validate_config()
                _pinecone_index = init_pinecone()
    return _pinecone_index


def stream_gemini_text_response(response_generator):
    """
    Stream generator function for Gemini text responses.
    Similar to ai_route.py streaming function.
    """
    try:
        for chunk in response_generator:
            if chunk:
                yield chunk
    except Exception as e:
        yield f"\n[Error streaming response: {str(e)}]"


@flim_frame_bp.route('/api/flim-frame/ask', methods=['POST'])
def ask_question_api():
    """
    API endpoint to ask questions about books.
    Uses Pinecone retrieval and Gemini for answer generation.
    Returns streaming response like ai_route.py
    """
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        # Get Pinecone index (lazy initialization)
        index = get_pinecone_index()
        
        # Ask question with streaming enabled
        response_generator = ask_question(question, index, stream=True)
        
        # Return streaming response
        return Response(stream_gemini_text_response(response_generator), mimetype='text/plain')
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@flim_frame_bp.route('/api/flim-frame/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Validate config
        validate_config()
        return jsonify({
            'status': 'healthy',
            'service': 'flim-frame-ai',
            'pinecone_index': PINECONE_INDEX
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@flim_frame_bp.route('/api/flim-frame/test-pinecone', methods=['GET'])
def test_pinecone():
    """Test Pinecone connection."""
    try:
        validate_config()
        index = init_pinecone()
        # Try a simple query to test connection
        test_query = "test"
        test_vec = embed_texts_genai([test_query])[0]
        
        # Query with minimal top_k
        res = index.query(
            vector=test_vec,
            top_k=1,
            include_metadata=False
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Pinecone connection successful',
            'index': PINECONE_INDEX,
            'test_query_result': 'Connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500