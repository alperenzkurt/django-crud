# Frontend Assets Organization

This folder contains the frontend assets for the application, organized into subdirectories:

## Structure

- `/css/` - Contains stylesheets
  - `main.css` - Main application styles

- `/js/` - Contains JavaScript files
  - `main.js` - Core utility functions and AJAX helpers
  - `accounts.js` - User management functionality
  - (Other feature-specific JS files will be added here)

## How to Use

### Adding New JavaScript Features

1. Create a new feature-specific JS file in the `/js/` directory
2. Add the file to the relevant template using the `extra_js` block:

```html
{% block extra_js %}
    {% load static %}
    <script src="{% static 'js/yourfile.js' %}"></script>
{% endblock %}
```

### Adding New CSS

1. Add your custom styles to `main.css`
2. For feature-specific styles, create a new CSS file and include it in your specific template:

```html
{% block extra_css %}
    {% load static %}
    <link href="{% static 'css/yourfile.css' %}" rel="stylesheet">
{% endblock %}
```

## Best Practices

1. Keep JavaScript modular and organized by feature
2. Use the AJAX utility functions in `main.js` for all API calls
3. Follow the naming conventions:
   - Feature-specific files: `featurename.js`
   - Shared utilities: prefix with `util-`
4. Add documentation to your JavaScript files 