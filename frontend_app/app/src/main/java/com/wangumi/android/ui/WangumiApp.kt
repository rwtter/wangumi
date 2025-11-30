package com.wangumi.android.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import com.wangumi.android.MainViewModel
import com.wangumi.android.ui.screens.HomeScreen
import com.wangumi.android.ui.theme.WangumiTheme

@Composable
fun WangumiApp(viewModel: MainViewModel) {
    val animeState by viewModel.animeListState.collectAsState()
    val filters by viewModel.animeFilters.collectAsState()
    val screen by viewModel.currentScreen.collectAsState()
    val detailState by viewModel.animeDetailState.collectAsState()
    val createForm by viewModel.createForm.collectAsState()
    val createState by viewModel.createAnimeState.collectAsState()
    val canCreate by viewModel.canCreate.collectAsState()
    val editorState by viewModel.editorRecommendations.collectAsState()
    val hotState by viewModel.hotRecommendations.collectAsState()

    WangumiTheme {
        HomeScreen(
            onLogin = viewModel::login,
            animeState = animeState,
            filters = filters,
            onSortChange = viewModel::selectSort,
            onCategoryInput = viewModel::updateCategoryInput,
            onApplyCategory = viewModel::applyCategoryFilter,
            onNextPage = viewModel::nextPage,
            onPrevPage = viewModel::previousPage,
            currentScreen = screen,
            editorState = editorState,
            hotState = hotState,
            onShowList = viewModel::showList,
            onShowRecommend = viewModel::showRecommend,
            onShowSocial = viewModel::showSocial,
            onShowHome = viewModel::showHome,
            onShowCreate = viewModel::openCreate,
            onAnimeClick = viewModel::openDetail,
            detailState = detailState,
            createForm = createForm,
            onUpdateCreateForm = viewModel::updateCreateForm,
            onSubmitCreate = viewModel::submitAnimeCreation,
            createState = createState,
            canCreate = canCreate
        )
    }
}
