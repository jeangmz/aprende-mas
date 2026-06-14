import os
import sys
from typing import List
from llama_cpp import Llama


def _unescape(val: str) -> str:
    return val.replace('\\n', '\n').replace('\\t', '\t')


def parse_toon(content: str) -> dict:
    result = {}
    section = None
    subsection = None

    for line in content.strip().split('\n'):
        line = line.rstrip()
        if not line or line.startswith('#'):
            continue

        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if indent == 0:
            key = stripped.rstrip(':')
            section = key
            subsection = None
            result[section] = {}
        elif indent == 2:
            if stripped.startswith('- '):
                continue
            key, _, val = stripped.partition(':')
            key = key.strip()
            raw = val.strip()
            val = raw.strip('"\'')
            if not val:
                subsection = key
                result[section][subsection] = [] if key == 'instructions' else {}
            else:
                result[section][key] = _unescape(val)
                subsection = None
        elif indent == 4 and section:
            if stripped.startswith('- '):
                result[section].setdefault('instructions', []).append(stripped[2:].strip())
            elif subsection:
                key, _, val = stripped.partition(':')
                result[section][subsection][key.strip()] = _unescape(val.strip().strip('"\''))

    return result


def load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "prompts.toon")
    with open(config_path, "r", encoding="utf-8") as f:
        return parse_toon(f.read())


class ChatEngine:
    def __init__(self, model_path: str = None):
        self.model_path = self._find_model(model_path)
        self.model_name = os.path.basename(self.model_path)
        self.config = load_config()
        self._apply_template()
        self.model = self._load_model()

    def _detect_model_type(self) -> str:
        name = self.model_name.lower()
        if "qwen" in name:
            return "qwen"
        if "phi" in name:
            return "phi-3"
        return "default"

    def _apply_template(self):
        model_type = self._detect_model_type()
        templates = self.config.get("chat_templates", {})
        template = templates.get(model_type)
        if not template:
            return
        conv = self.config.setdefault("conversation", {})
        for key in ("user_tag", "assistant_tag", "end_tag", "stop_tokens", "system_prefix", "system_suffix"):
            if key in template:
                conv[key] = template[key]

    def _find_model(self, model_path: str | None = None) -> str:
        env_model = os.environ.get("LEXIMIND_MODEL")

        if model_path and os.path.exists(model_path):
            if os.path.isdir(model_path):
                models = [f for f in os.listdir(model_path) if f.endswith('.gguf')]
                if env_model:
                    match = [m for m in models if env_model.lower() in m.lower()]
                    if match:
                        return os.path.join(model_path, match[0])
                if models:
                    return os.path.join(model_path, models[0])
            else:
                return model_path

        search_dirs = []
        if getattr(sys, 'frozen', False):
            search_dirs.append(os.path.dirname(sys.executable))
        else:
            search_dirs.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        for base_dir in search_dirs:
            model_dir = os.path.join(base_dir, "model")
            if os.path.isdir(model_dir):
                models = [f for f in os.listdir(model_dir) if f.endswith('.gguf')]
                if env_model:
                    match = [m for m in models if env_model.lower() in m.lower()]
                    if match:
                        return os.path.join(model_dir, match[0])
                if models:
                    return os.path.join(model_dir, models[0])

        raise FileNotFoundError("No .gguf model found. Place a model file in the 'model/' folder.")

    def _load_model(self):
        return Llama(
            model_path=self.model_path,
            n_ctx=2048,
            n_threads=6,
            verbose=False
        )

    def _build_system(self) -> str:
        conv = self.config.get("conversation", {})
        prefix = conv.get("system_prefix", "<|system|>") or ""
        suffix = conv.get("system_suffix", "<|end|>") or ""

        instructions = self.config.get("system", {}).get("instructions", [])
        if isinstance(instructions, str):
            instructions = [instructions]
        desc = self.config.get("system", {}).get("description", "English tutor for Spanish-speaking children")
        intro = f"I am Aprende+, {desc}."
        examples = (
            "\n\nEXAMPLES of correct responses:"
            "\n# When user asks for English content -> respond ONLY in English:"
            "\nUser: dime oraciones en ingles"
            "\nAssistant: I like to play soccer."
            "\nMy name is John."
            "\nI have a big dog."
            "\n"
            "\nUser: los numeros del 1 al 10 en ingles"
            "\nAssistant: One, Two, Three, Four, Five, Six, Seven, Eight, Nine, Ten"
            "\n"
            "\nUser: dame un cuento largo en ingles"
            "\nAssistant: Once upon a time in a small village, there lived a little girl named Lily..."
            "\n"
            "\n# When user asks an explanation in Spanish -> explain in Spanish:"
            "\nUser: como se usa el verbo to be"
            "\nAssistant: El verbo 'to be' significa 'ser' o 'estar'. Se conjuga así: I am (yo soy/estoy), you are (tú eres/estás), he/she/it is (él/ella es/está), we are (nosotros somos/estamos), they are (ellos son/están). Por ejemplo: I am a student. She is happy."
            "\n"
            "\n# When user speaks spanglish -> reply in spanglish:"
            "\nUser: quiero aprender los colores in english"
            "\nAssistant: Claro! Los colors in English son: red (rojo), blue (azul), green (verde), yellow (amarillo), black (negro), white (blanco)."
        )
        all_instructions = [intro] + instructions + [examples]
        body = "\n".join(all_instructions)
        return prefix + body + suffix

    def _format_history(self, history: List[dict]) -> str:
        conv = self.config.get("conversation", {})
        user_tag = conv.get("user_tag", "<|user|>") or "<|user|>"
        assistant_tag = conv.get("assistant_tag", "<|assistant|>") or "<|assistant|>"
        end_tag = conv.get("end_tag", "<|end|>") or "<|end|>"

        lines = []
        for msg in history:
            lines.append(f"{user_tag}{msg['user']}{end_tag}")
            lines.append(f"{assistant_tag}{msg['assistant']}{end_tag}")

        return "\n".join(lines)

    def generate_title(self, first_message: str) -> str:
        msg = first_message[:80].lower().strip()
        keywords = self.config.get("title", {}).get("keywords", {})

        for key, title in keywords.items():
            if key in msg:
                return title

        words = msg.split()[:4]
        title = " ".join(word.capitalize() for word in words if len(word) > 2)

        if len(first_message) <= 30:
            return first_message.strip()

        return title if title else "Chat"

    def _build_prompt(self, user_message: str, conversation_history: List[dict]) -> str:
        conv = self.config.get("conversation", {})
        user_tag = conv.get("user_tag", "<|user|>") or "<|user|>"
        end_tag = conv.get("end_tag", "<|end|>") or "<|end|>"
        assistant_tag = conv.get("assistant_tag", "<|assistant|>") or "<|assistant|>"
        max_context = int(conv.get("max_context", 6))
        context = self._format_history(conversation_history[-max_context:])
        return (
            self._build_system() + "\n"
            + context + "\n"
            + f"{user_tag}{user_message}{end_tag}\n"
            + f"{assistant_tag}"
        )

    def generate_response(self, user_message: str, conversation_history: List[dict]) -> str:
        conv = self.config.get("conversation", {})
        assistant_tag = conv.get("assistant_tag", "<|assistant|>") or "<|assistant|>"
        end_tag = conv.get("end_tag", "<|end|>") or "<|end|>"
        stop_str = conv.get("stop_tokens", "<|user|>,<|end|>")
        stop_tokens = [s.strip() for s in stop_str.split(',')]

        prompt = self._build_prompt(user_message, conversation_history)

        response = self.model(
            prompt,
            max_tokens=600,
            temperature=0.7,
            top_p=0.9,
            stop=stop_tokens
        )

        result = response["choices"][0]["text"].strip()
        result = result.replace(assistant_tag, "").replace(end_tag, "").strip()

        return result

    def generate_stream(self, user_message: str, conversation_history: List[dict]):
        conv = self.config.get("conversation", {})
        assistant_tag = conv.get("assistant_tag", "<|assistant|>") or "<|assistant|>"
        end_tag = conv.get("end_tag", "<|end|>") or "<|end|>"
        stop_str = conv.get("stop_tokens", "<|user|>,<|end|>")
        stop_tokens = [s.strip() for s in stop_str.split(',')]

        prompt = self._build_prompt(user_message, conversation_history)

        stream = self.model(
            prompt,
            max_tokens=600,
            temperature=0.7,
            top_p=0.9,
            stop=stop_tokens,
            stream=True
        )

        for output in stream:
            token = output["choices"][0]["text"]
            if not token:
                continue
            filtered = token.replace(assistant_tag, "").replace(end_tag, "")
            if filtered:
                yield filtered
