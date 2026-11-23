import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"================================================================")
    print(f" BharatPath - Ancient Indian Routes, Trade & Heritage Platform")
    print(f" Running on http://127.0.0.1:{port}")
    print(f" Theme: Indian Knowledge Systems (IKS)")
    print(f"================================================================")
    app.run(host='127.0.0.1', port=port, debug=True)
