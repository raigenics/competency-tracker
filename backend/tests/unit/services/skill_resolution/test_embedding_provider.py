"""
Unit tests for embedding providers.

Tests OpenAI, Azure OpenAI, and Fake embedding providers.
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock

from app.services.skill_resolution.embedding_provider import (
    OpenAIEmbeddingProvider,
    AzureOpenAIEmbeddingProvider,
    FakeEmbeddingProvider,
    create_embedding_provider
)


class TestOpenAIEmbeddingProvider:
    """Test suite for OpenAIEmbeddingProvider."""
    
    def test_init_with_api_key(self):
        """Should initialize with provided API key."""
        provider = OpenAIEmbeddingProvider(api_key="test-key", model="test-model")
        assert provider.api_key == "test-key"
        assert provider.model == "test-model"
    
    def test_init_with_env_var(self):
        """Should initialize with API key from environment variable."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            provider = OpenAIEmbeddingProvider()
            assert provider.api_key == "env-key"
    
    def test_init_without_api_key_raises_error(self):
        """Should raise ValueError when API key not provided and env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not provided"):
                OpenAIEmbeddingProvider()
    
    @patch('app.services.skill_resolution.embedding_provider.OpenAI')
    def test_embed_success(self, mock_openai_class):
        """Should successfully generate embedding."""
        # Arrange
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAIEmbeddingProvider(api_key="test-key")
        
        # Act
        result = provider.embed("test text")
        
        # Assert
        assert result == [0.1, 0.2, 0.3]
        mock_client.embeddings.create.assert_called_once_with(
            input="test text",
            model="text-embedding-3-small"
        )
    
    @patch('app.services.skill_resolution.embedding_provider.OpenAI')
    def test_embed_exception(self, mock_openai_class):
        """Should raise exception when API call fails."""
        # Arrange
        mock_client = Mock()
        mock_client.embeddings.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        provider = OpenAIEmbeddingProvider(api_key="test-key")
        
        # Act & Assert
        with pytest.raises(Exception, match="API Error"):
            provider.embed("test text")


class TestAzureOpenAIEmbeddingProvider:
    """Test suite for AzureOpenAIEmbeddingProvider."""
    
    def test_init_with_credentials(self):
        """Should initialize with provided credentials."""
        provider = AzureOpenAIEmbeddingProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="test-deployment"
        )
        assert provider.api_key == "test-key"
        assert provider.endpoint == "https://test.openai.azure.com"
        assert provider.deployment == "test-deployment"
    
    def test_init_with_env_vars(self):
        """Should initialize with credentials from environment variables."""
        with patch.dict(os.environ, {
            "AZURE_OPENAI_API_KEY": "env-key",
            "AZURE_OPENAI_ENDPOINT": "https://env.openai.azure.com",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "env-deployment"
        }):
            provider = AzureOpenAIEmbeddingProvider()
            assert provider.api_key == "env-key"
            assert provider.endpoint == "https://env.openai.azure.com"
            assert provider.deployment == "env-deployment"
    
    def test_init_without_api_key_raises_error(self):
        """Should raise ValueError when API key not provided."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Azure OpenAI API key not provided"):
                AzureOpenAIEmbeddingProvider()
    
    def test_init_without_endpoint_raises_error(self):
        """Should raise ValueError when endpoint not provided."""
        with patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "key"}, clear=True):
            with pytest.raises(ValueError, match="Azure OpenAI endpoint not provided"):
                AzureOpenAIEmbeddingProvider()
    
    @patch('app.services.skill_resolution.embedding_provider.AzureOpenAI')
    def test_embed_success(self, mock_azure_class):
        """Should successfully generate embedding."""
        # Arrange
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.4, 0.5, 0.6])]
        mock_client.embeddings.create.return_value = mock_response
        mock_azure_class.return_value = mock_client
        
        provider = AzureOpenAIEmbeddingProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="test-deployment"
        )
        
        # Act
        result = provider.embed("azure test")
        
        # Assert
        assert result == [0.4, 0.5, 0.6]
        mock_client.embeddings.create.assert_called_once_with(
            input="azure test",
            model="test-deployment"
        )
    
    @patch('app.services.skill_resolution.embedding_provider.AzureOpenAI')
    def test_embed_exception(self, mock_azure_class):
        """Should raise exception when API call fails."""
        # Arrange
        mock_client = Mock()
        mock_client.embeddings.create.side_effect = Exception("Azure API Error")
        mock_azure_class.return_value = mock_client
        
        provider = AzureOpenAIEmbeddingProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com"
        )
        
        # Act & Assert
        with pytest.raises(Exception, match="Azure API Error"):
            provider.embed("test text")


class TestFakeEmbeddingProvider:
    """Test suite for FakeEmbeddingProvider."""
    
    def test_init_default(self):
        """Should initialize with default parameters."""
        provider = FakeEmbeddingProvider()
        assert provider.dimension == 1536
        assert provider.deterministic is True
    
    def test_init_custom_dimension(self):
        """Should initialize with custom dimension."""
        provider = FakeEmbeddingProvider(dimension=512)
        assert provider.dimension == 512
    
    def test_embed_returns_correct_dimension(self):
        """Should return embedding with correct dimension."""
        provider = FakeEmbeddingProvider(dimension=128)
        embedding = provider.embed("test")
        assert len(embedding) == 128
    
    def test_embed_deterministic(self):
        """Same text should return same embedding when deterministic."""
        provider = FakeEmbeddingProvider(deterministic=True)
        embedding1 = provider.embed("python")
        embedding2 = provider.embed("python")
        assert embedding1 == embedding2
    
    def test_embed_different_texts_different_embeddings(self):
        """Different texts should return different embeddings."""
        provider = FakeEmbeddingProvider(deterministic=True)
        embedding1 = provider.embed("python")
        embedding2 = provider.embed("javascript")
        assert embedding1 != embedding2
    
    def test_embed_non_deterministic(self):
        """Non-deterministic mode should generate random embeddings."""
        provider = FakeEmbeddingProvider(deterministic=False)
        embedding1 = provider.embed("test")
        embedding2 = provider.embed("test")
        # High probability they'll be different (not guaranteed but very likely)
        assert len(embedding1) == len(embedding2)
        assert all(0 <= v <= 1 for v in embedding1)
    
    def test_embed_caches_deterministic_results(self):
        """Should cache results in deterministic mode."""
        provider = FakeEmbeddingProvider(deterministic=True)
        text = "cached_text"
        
        # First call
        embedding1 = provider.embed(text)
        assert text in provider._cache
        
        # Second call should use cache
        embedding2 = provider.embed(text)
        assert embedding1 == embedding2
        assert embedding2 is provider._cache[text]


class TestCreateEmbeddingProvider:
    """Test suite for create_embedding_provider factory."""
    
    @patch('app.services.skill_resolution.embedding_provider.OpenAI')
    def test_create_openai_provider(self, mock_openai_class):
        """Should create OpenAI provider."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            provider = create_embedding_provider(provider_type="openai")
            assert isinstance(provider, OpenAIEmbeddingProvider)
    
    @patch('app.services.skill_resolution.embedding_provider.AzureOpenAI')
    def test_create_azure_provider(self, mock_azure_class):
        """Should create Azure OpenAI provider."""
        with patch.dict(os.environ, {
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com"
        }):
            provider = create_embedding_provider(provider_type="azure_openai")
            assert isinstance(provider, AzureOpenAIEmbeddingProvider)
    
    def test_create_fake_provider(self):
        """Should create fake provider."""
        provider = create_embedding_provider(provider_type="fake")
        assert isinstance(provider, FakeEmbeddingProvider)
    
    @patch('app.services.skill_resolution.embedding_provider.AzureOpenAI')
    def test_create_default_provider(self, mock_azure_class):
        """Should default to azure_openai when provider_type not specified."""
        # Need to clear EMBEDDING_PROVIDER env var to test default behavior
        import os
        env_backup = os.environ.copy()
        # Clear any existing EMBEDDING_PROVIDER setting
        if 'EMBEDDING_PROVIDER' in os.environ:
            del os.environ['EMBEDDING_PROVIDER']
        try:
            with patch.dict(os.environ, {
                "AZURE_OPENAI_API_KEY": "test-key",
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com"
            }, clear=False):
                provider = create_embedding_provider()
                assert isinstance(provider, AzureOpenAIEmbeddingProvider)
        finally:
            os.environ.clear()
            os.environ.update(env_backup)
    
    def test_create_unknown_provider_raises_error(self):
        """Should raise ValueError for unknown provider type."""
        with pytest.raises(ValueError, match="Unknown embedding provider type"):
            create_embedding_provider(provider_type="unknown")
    
    @patch('app.services.skill_resolution.embedding_provider.AzureOpenAI')
    def test_create_from_env_var(self, mock_azure_class):
        """Should use EMBEDDING_PROVIDER env var when not specified."""
        with patch.dict(os.environ, {
            "EMBEDDING_PROVIDER": "azure_openai",
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com"
        }):
            provider = create_embedding_provider()
            assert isinstance(provider, AzureOpenAIEmbeddingProvider)
