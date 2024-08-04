from transformers import pipeline

class AIModel:
    def __init__(self):
        """Инициализация модели GPT-2."""
        self.text_generator = pipeline("text-generation", model="gpt2")

    def generate_text(self, input_text, max_length=50, num_return_sequences=1):
        """Генерация текста на основе входного текста."""
        response = self.text_generator(input_text, max_length=max_length, num_return_sequences=num_return_sequences)
        return response[0]['generated_text']
