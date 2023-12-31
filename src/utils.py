from transformers import BertTokenizer, TFAutoModel
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor, Wav2Vec2FeatureExtractor
import torch
import torchaudio
import numpy as np

class Functions:
    def __init__(self, audio_file: str = ""):
        """
        Initializes the Functions class with an optional audio_file parameter.
        The initialization triggers various functions to process the audio file and generate a concatenated vector.

        Parameters:
        - audio_file (str): Path to the audio file.
        
        Attributes:
        - audio_file (str): Path to the audio file.
        - concatenated_vector_get (numpy.ndarray): Concatenated vector representing the audio content.

        Returns:
        None
        """
        self.audio_file = audio_file
        characters_get = self.transcribe_audio(audio_file)
        convert_audio_to_matrix_get = self.convert_audio_to_matrix(audio_file)
        matrix_to_one_vector_get = self.matrix_to_one_vector(convert_audio_to_matrix_get)
        generate_ambidig_vector_get = self.generate_embedding_vector(characters_get)
        self.concatenated_vector_get = self.vector_concatenation(generate_ambidig_vector_get, matrix_to_one_vector_get)

    def get_concatenated_vector_get(self):
        """
        Returns the concatenated vector representing the audio content.

        Returns:
        numpy.ndarray: Concatenated vector.
        """
        return self.concatenated_vector_get
    
    def convert_audio_to_matrix(self, audio_file):
        """
        Converts the audio file to a matrix representation using Wav2Vec2 feature extraction.

        Parameters:
        - audio_file (str): Path to the audio file.

        Returns:
        torch.Tensor: Matrix representation of the audio content.
        """
        feature_extractor = Wav2Vec2FeatureExtractor(feature_size=1, sampling_rate=16000)
        audio_input, sample_rate = torchaudio.load(audio_file)
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(sample_rate, 16000)
            audio_input = resampler(audio_input)
            sample_rate = 16000
        audio_features = feature_extractor(
            audio_input,
            sampling_rate=sample_rate,
            padding=True,
            return_tensors="pt"
        )
        matrix = audio_features.input_values.squeeze(0)
        return matrix
    
    def matrix_to_one_vector(self, matrix):
        """
        Converts a matrix to a one-dimensional vector by calculating the mean along the specified dimension.

        Parameters:
        - matrix (torch.Tensor): Matrix representation of the audio content.

        Returns:
        torch.Tensor: One-dimensional vector.
        """
        mean_vector = torch.mean(matrix, dim=0)
        return mean_vector

    def generate_embedding_vector(self, transcript):
        """
        Generates an embedding vector using BERT-based tokenizer and model for the given transcript.

        Parameters:
        - transcript (str): Transcription of the audio content.

        Returns:
        numpy.ndarray: Embedding vector.
        """
        tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        model = TFAutoModel.from_pretrained('bert-base-uncased')
        inputs = tokenizer.encode_plus(transcript, add_special_tokens=True, return_tensors='tf')
        outputs = model(inputs['input_ids'])
        embedding_vector = outputs.last_hidden_state[:, 0, :].numpy()
        return embedding_vector

    def vector_concatenation(self, bert_vector, wav2vec_matrix):
        """
        Concatenates the BERT-based vector and Wav2Vec2 matrix along the appropriate axis.

        Parameters:
        - bert_vector (numpy.ndarray): BERT-based embedding vector.
        - wav2vec_matrix (numpy.ndarray): Matrix representation of the audio content.

        Returns:
        numpy.ndarray: Concatenated vector.
        """
        m = wav2vec_matrix.shape[0]
        n = bert_vector.shape[0]
        if wav2vec_matrix.ndim == 1:
            wav2vec_matrix = np.expand_dims(wav2vec_matrix, axis=1)
        bert_vector = np.tile(bert_vector, (m, 1))
        concatenated_vector = np.concatenate((wav2vec_matrix, bert_vector), axis=1)
        return concatenated_vector

    def transcribe_audio(self, audio_path):
        """
        Transcribes the audio content using the Wav2Vec2 model.

        Parameters:
        - audio_path (str): Path to the audio file.

        Returns:
        str: Transcription of the audio content.
        """
        model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
        tokenizer = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
        waveform, sample_rate = torchaudio.load(audio_path)
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(sample_rate, 16000)
            waveform = resampler(waveform)
        input_values = tokenizer(waveform[0], return_tensors="pt").input_values
        logits = model(input_values).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = tokenizer.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        return transcription
