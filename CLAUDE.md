# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Wangumi** is a comprehensive anime tracking and social platform built with Django backend and Vue.js frontend. Users can track anime watching status, rate and review anime, follow other users, and discover new anime through recommendations.

## Technology Stack

**Backend:** Django 5.2.7 with Django REST Framework, PostgreSQL, Redis, JWT authentication
**Frontend:** Vue 3 with TypeScript, Vite, Vue Router 4, Axios

## Common Development Commands

### Backend Development
```bash
cd backend

# Start development server
python manage.py runserver

# Database operations
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Run tests
python manage.py test wangumi_app.tests

# Collect static files (for production)
python manage.py collectstatic
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Placeholder Frontend (for API testing)
```bash
cd frontend
python -m http.server 3000
```

## Architecture Overview

### Backend Structure
The Django backend follows a modular architecture with clean separation of concerns:

- **Dynamic URL Loading**: The main `urls.py` automatically imports `_url.py` files from each app directory
- **Feature-based Organization**: Views and URLs are organized by feature (login, reviews, anime, recommendations)
- **RESTful API Design**: Consistent JSON response format with `{code, message, data}` structure
- **JWT Authentication**: SimpleJWT for token-based authentication with refresh tokens

### Key Backend Modules
- `wangumi_app/views/anime_views.py` - Anime CRUD and listing operations
- `wangumi_app/views/reviews_view.py` - Review and rating system
- `wangumi_app/views/watch_status_view.py` - User anime tracking status
- `wangumi_app/views/recommend_*.py` - Recommendation algorithms
- `wangumi_app/models.py` - Comprehensive database models for anime, users, characters, staff

### Frontend Structure
- **Component-based**: Vue components for different UI sections
- **Service Layer**: API integration through `services/animeService.js`
- **TypeScript Support**: Type-safe development with Vue 3 + TypeScript

## Database Schema

The application uses a comprehensive database design with:
- Multi-language support for anime titles and descriptions
- Generic foreign keys for flexible comment/reply systems
- User privacy controls and social features (following, likes, reports)
- Rich metadata for anime, characters, and staff information

## Development Standards

### Code Style (Python)
- Follow PEP 8 guidelines
- Functions and variables: camelCase (`getUserInfo`)
- Classes: PascalCase (`UserProfile`)
- Database tables: snake_case (`user_profile`)
- Include docstrings for all functions

### Git Workflow
- `main`: Stable deployable version
- `dev`: Development integration branch
- `feature/<module>`: New features
- `fix/<issue>`: Bug fixes
- Commit format: `feat(user): add login API`

### API Standards
- RESTful endpoints with consistent patterns
- Standard response format:
```json
{
  "code": 0,
  "message": "success",
  "data": {...}
}
```
- Use Apifox for API documentation and mock data

### Testing Requirements
- Write unit tests for critical paths (login, registration, main data flows)
- Use Django's built-in `unittest` or `pytest-django`
- Test APIs before commits using Apifox

## Environment Configuration

The backend uses environment variables for configuration. Key settings include:
- Database connection (PostgreSQL)
- Redis connection for caching
- JWT token settings
- CORS configuration

## Development Tips

1. **Start with models**: The database schema is comprehensive and well-designed
2. **Follow URL patterns**: New features should have their own `_url.py` files
3. **Use the dynamic URL loading**: The system automatically discovers URL modules
4. **Test with placeholder frontend**: Use the simple HTML frontend to verify APIs
5. **Maintain API documentation**: Keep Apifox docs updated with new endpoints
6. **Social features**: The platform includes following, recommendations, and user activities
7. **Multi-language support**: Consider internationalization in user-facing features