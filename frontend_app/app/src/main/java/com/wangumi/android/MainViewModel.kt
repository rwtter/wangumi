package com.wangumi.android

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.wangumi.android.data.model.AnimeCreateRequest
import com.wangumi.android.data.model.AnimeDetailResult
import com.wangumi.android.data.model.AnimeListResult
import com.wangumi.android.data.model.LoginRequest
import com.wangumi.android.data.model.RecommendationResult
import com.wangumi.android.data.remote.BackendRepository
import com.wangumi.android.data.remote.NetworkResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class MainViewModel(
    private val repository: BackendRepository = BackendRepository()
) : ViewModel() {

    data class AnimeFilters(
        val sort: String = "热度",
        val categoryInput: String = "",
        val page: Int = 1,
        val limit: Int = 12
    )

    private val _animeFilters = MutableStateFlow(AnimeFilters())
    val animeFilters: StateFlow<AnimeFilters> = _animeFilters

    private val _animeListState =
        MutableStateFlow<NetworkResult<AnimeListResult>>(NetworkResult.Loading)
    val animeListState: StateFlow<NetworkResult<AnimeListResult>> = _animeListState

    private val _editorRecommendations =
        MutableStateFlow<NetworkResult<RecommendationResult>>(NetworkResult.Loading)
    val editorRecommendations: StateFlow<NetworkResult<RecommendationResult>> = _editorRecommendations

    private val _hotRecommendations =
        MutableStateFlow<NetworkResult<RecommendationResult>>(NetworkResult.Loading)
    val hotRecommendations: StateFlow<NetworkResult<RecommendationResult>> = _hotRecommendations

    sealed interface Screen {
        data object List : Screen
        data object Recommend : Screen
        data object Social : Screen
        data object Home : Screen
        data class Detail(val animeId: Int) : Screen
        data object Create : Screen
    }

    private val _currentScreen = MutableStateFlow<Screen>(Screen.List)
    val currentScreen: StateFlow<Screen> = _currentScreen

    private val _animeDetailState =
        MutableStateFlow<NetworkResult<AnimeDetailResult>?>(null)
    val animeDetailState: StateFlow<NetworkResult<AnimeDetailResult>?> = _animeDetailState

    data class CreateAnimeForm(
        val title: String = "",
        val titleJapanese: String = "",
        val summary: String = "",
        val categoryInput: String = "",
        val releaseDate: String = "",
        val status: String = "",
        val totalEpisodes: String = "",
        val coverUrl: String = ""
    )

    private val _createForm = MutableStateFlow(CreateAnimeForm())
    val createForm: StateFlow<CreateAnimeForm> = _createForm

    private val _createAnimeState =
        MutableStateFlow<NetworkResult<Unit>?>(null)
    val createAnimeState: StateFlow<NetworkResult<Unit>?> = _createAnimeState

    private val _canCreate = MutableStateFlow(false)
    val canCreate: StateFlow<Boolean> = _canCreate

    init {
        loadAnimeList()
        refreshRecommendations()
    }

    fun loadAnimeList() {
        val filters = _animeFilters.value
        viewModelScope.launch {
            _animeListState.value = NetworkResult.Loading
            _animeListState.value = repository.getAnimeList(
                filters.sort,
                filters.categoryInput.split(',')
                    .map { it.trim() }
                    .filter { it.isNotBlank() },
                filters.page,
                filters.limit
            )
        }
    }

    fun selectSort(sort: String) {
        _animeFilters.value = _animeFilters.value.copy(sort = sort, page = 1)
        loadAnimeList()
    }

    fun updateCategoryInput(text: String) {
        _animeFilters.value = _animeFilters.value.copy(categoryInput = text)
    }

    fun applyCategoryFilter() {
        _animeFilters.value = _animeFilters.value.copy(page = 1)
        loadAnimeList()
    }

    fun nextPage() {
        val success = animeListState.value as? NetworkResult.Success ?: return
        val maxPage = success.data.pagination.pages
        val current = _animeFilters.value
        if (current.page >= maxPage) return
        _animeFilters.value = current.copy(page = current.page + 1)
        loadAnimeList()
    }

    fun previousPage() {
        val current = _animeFilters.value
        if (current.page <= 1) return
        _animeFilters.value = current.copy(page = current.page - 1)
        loadAnimeList()
    }

    fun login(username: String, password: String, onResult: (NetworkResult<Unit>) -> Unit) {
        viewModelScope.launch {
            onResult(NetworkResult.Loading)
            val result = repository.login(LoginRequest(username, password))
            onResult(result)
            if (result is NetworkResult.Success) {
                _canCreate.value = true
                refreshRecommendations()
                if (_currentScreen.value is Screen.Detail || _currentScreen.value is Screen.Create) {
                    changeTab(Screen.List)
                }
            }
        }
    }

    fun showList() = changeTab(Screen.List)

    fun showRecommend() = changeTab(Screen.Recommend)

    fun showSocial() = changeTab(Screen.Social)

    fun showHome() = changeTab(Screen.Home)

    fun openDetail(animeId: Int) {
        _currentScreen.value = Screen.Detail(animeId)
        viewModelScope.launch {
            _animeDetailState.value = NetworkResult.Loading
            _animeDetailState.value = repository.getAnimeDetail(animeId)
        }
    }

    fun openCreate() {
        _currentScreen.value = Screen.Create
        _createAnimeState.value = null
    }

    fun updateCreateForm(transform: (CreateAnimeForm) -> CreateAnimeForm) {
        _createForm.value = transform(_createForm.value)
    }

    fun submitAnimeCreation() {
        val form = _createForm.value
        if (form.title.isBlank()) {
            _createAnimeState.value = NetworkResult.Error("标题不能为空")
            return
        }
        val episodes = form.totalEpisodes.toIntOrNull()
        val categories = form.categoryInput.split(',')
            .map { it.trim() }
            .filter { it.isNotBlank() }

        viewModelScope.launch {
            _createAnimeState.value = NetworkResult.Loading
            val request = AnimeCreateRequest(
                title = form.title,
                title_cn = form.titleJapanese.ifBlank { null },
                description = form.summary.ifBlank { null },
                genres = if (categories.isEmpty()) null else categories,
                release_date = form.releaseDate.ifBlank { null },
                status = form.status.ifBlank { null },
                total_episodes = episodes,
                cover_url = form.coverUrl.ifBlank { null }
            )
            val result = repository.createAnime(request)
            _createAnimeState.value = when (result) {
                is NetworkResult.Success -> {
                    _createForm.value = CreateAnimeForm()
                    loadAnimeList()
                    changeTab(Screen.List)
                    NetworkResult.Success(Unit)
                }
                is NetworkResult.Error -> result
                NetworkResult.Loading -> NetworkResult.Loading
            }
        }
    }

    private fun changeTab(screen: Screen) {
        _currentScreen.value = screen
    }

    fun refreshRecommendations() {
        loadEditorPicks()
        loadHotRanking()
    }

    private fun loadEditorPicks() {
        viewModelScope.launch {
            _editorRecommendations.value = NetworkResult.Loading
            _editorRecommendations.value = repository.getRecommendations(page = 1, limit = 12)
        }
    }

    private fun loadHotRanking() {
        viewModelScope.launch {
            _hotRecommendations.value = NetworkResult.Loading
            _hotRecommendations.value = repository.getRecommendations(source = "hot", page = 1, limit = 15)
        }
    }
}
