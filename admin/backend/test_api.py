import requests
import json
import time
import traceback

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000"
ADMIN_BASE_URL = f"{BASE_URL}/admin"
TEST_USER = f"testuser_{int(time.time())}"
TEST_PASSWORD = "testpassword"

# --- Global State ---
auth_token = None

# --- Helper Functions ---
def get_auth_headers():
    """Returns authorization headers if a token is available."""
    if not auth_token:
        raise Exception("Auth token not available. Run registration and login first.")
    return {"Authorization": f"Bearer {auth_token}"}

def print_test_header(title):
    """Prints a formatted header for a test section."""
    print(f"\n{'='*20} {title} {'='*20}")

def print_response(response):
    """Prints the status code and JSON response."""
    print(f"Status Code: {response.status_code}")
    try:
        print("Response:", response.json())
    except json.JSONDecodeError:
        print("Response (non-JSON):", response.text)

# --- Test Functions ---

def test_01_register_user():
    """Tests user registration."""
    print_test_header("1. User Registration")
    url = f"{BASE_URL}/users/"
    data = {"username": TEST_USER, "password": TEST_PASSWORD}
    response = requests.post(url, json=data)
    print_response(response)
    assert response.status_code == 200, "User registration failed"
    print("User registration successful.")

def test_02_login():
    """Tests user login to get an access token."""
    global auth_token
    print_test_header("2. User Login")
    url = f"{BASE_URL}/token"
    data = {"username": TEST_USER, "password": TEST_PASSWORD}
    response = requests.post(url, data=data) # token endpoint expects form data
    print_response(response)
    assert response.status_code == 200, "User login failed"
    auth_token = response.json()["access_token"]
    assert auth_token, "Failed to get auth token"
    print("User login successful, token obtained.")

def test_03_read_current_user():
    """Tests fetching the current user's data."""
    print_test_header("3. Read Current User (/users/me/)")
    url = f"{BASE_URL}/users/me/"
    response = requests.get(url, headers=get_auth_headers())
    print_response(response)
    assert response.status_code == 200
    assert response.json()["username"] == TEST_USER

def test_04_admin_endpoints():
    """Tests various admin-related endpoints."""
    print_test_header("4. Admin Endpoints")
    headers = get_auth_headers()

    # Test Audit Logs
    print("\n--- Testing Audit Logs ---")
    url = f"{BASE_URL}/audit-logs/" # Corrected URL
    response = requests.get(url, headers=headers)
    print_response(response)
    assert response.status_code == 200

    # Test Dashboard Stats
    print("\n--- Testing Dashboard Stats ---")
    url = f"{BASE_URL}/dashboard/stats" # Corrected URL
    response = requests.get(url, headers=headers)
    print_response(response)
    assert response.status_code == 200

def test_05_images_api():
    """Tests the images API (which uses fake data)."""
    print_test_header("5. Images API")
    url_base = f"{BASE_URL}/images/" # Corrected URL
    headers = get_auth_headers()

    # Get all images
    print("\n--- Testing Get All Images ---")
    response = requests.get(url_base, headers=headers)
    print_response(response)
    assert response.status_code == 200
    
    # Get one image
    print("\n--- Testing Get One Image ---")
    image_id = "img001" 
    response = requests.get(f"{url_base}{image_id}", headers=headers)
    print_response(response)
    assert response.status_code == 200

    # Delete an image
    print("\n--- Testing Delete Image ---")
    image_id_to_delete = "img002"
    response = requests.delete(f"{url_base}{image_id_to_delete}", headers=headers)
    print_response(response)
    assert response.status_code == 200

def test_06_inspirations_crud():
    """Tests full CRUD for the inspirations API."""
    print_test_header("6. Inspirations API (CRUD)")
    url_base = f"{BASE_URL}/inspirations/" # Corrected URL
    headers = get_auth_headers()
    inspiration_id = None

    try:
        # Create
        print("\n--- Testing Create Inspiration ---")
        create_data = {"image_id": "123", "user_id": "1"} # Example data
        response = requests.post(url_base, json=create_data, headers=headers)
        print_response(response)
        assert response.status_code == 200
        inspiration_id = response.json()["id"]
        assert inspiration_id

        # Read (one)
        print("\n--- Testing Read One Inspiration ---")
        response = requests.get(f"{url_base}{inspiration_id}", headers=headers)
        print_response(response)
        assert response.status_code == 200
        assert response.json()["id"] == inspiration_id

        # Read (all)
        print("\n--- Testing Read All Inspirations ---")
        response = requests.get(url_base, headers=headers)
        print_response(response)
        assert response.status_code == 200
        inspirations = response.json()
        assert isinstance(inspirations, list)
        # Since we just created one, it should be at least one.
        assert any(insp["id"] == inspiration_id for insp in inspirations)
        print("Inspirations fetched successfully.")

        # Update
        print("\n--- Testing Update Inspiration ---")
        update_data = {"image_id": 456, "user_id": "2"}
        response = requests.put(f"{url_base}{inspiration_id}", json=update_data, headers=headers)
        print_response(response)
        assert response.status_code == 200
        assert response.json()["image_id"] == 456

    finally:
        # Delete
        if inspiration_id:
            print("\n--- Testing Delete Inspiration ---")
            response = requests.delete(f"{url_base}{inspiration_id}", headers=headers)
            print_response(response)
            assert response.status_code == 200

def test_07_tasks_api():
    """Tests the tasks API (which uses fake data)."""
    print_test_header("7. Tasks API")
    url_base = f"{BASE_URL}/tasks" # Corrected URL
    headers = get_auth_headers()

    print("\n--- Testing Get Task Queue ---")
    response = requests.get(f"{url_base}/queue", headers=headers)
    print_response(response)
    assert response.status_code == 200

    print("\n--- Testing Get Task History ---")
    response = requests.get(f"{url_base}/history", headers=headers)
    print_response(response)
    assert response.status_code == 200

    print("\n--- Testing Get Task Details ---")
    task_id = "task123"
    response = requests.get(f"{url_base}/{task_id}", headers=headers)
    print_response(response)
    assert response.status_code == 200

def test_08_workflows_crud():
    """Tests CRUD for workflows."""
    print_test_header("8. Workflows API (CRUD)")
    url = f"{ADMIN_BASE_URL}/workflows/"
    headers = get_auth_headers()

    # Create
    print("\n--- Testing Create Workflow ---")
    workflow_data = {"name": "My Test Workflow", "description": "A test", "workflow_json": {"a": 1}}
    response = requests.post(url, json=workflow_data, headers=headers)
    print_response(response)
    assert response.status_code == 200
    workflow_id = response.json()["id"]

    # Read
    print("\n--- Testing Read Workflows ---")
    response = requests.get(url, headers=headers)
    print_response(response)
    assert response.status_code == 200
    assert any(wf["id"] == workflow_id for wf in response.json())

def test_09_prompts_crud():
    """Tests CRUD for prompts."""
    print_test_header("9. Prompts API (CRUD)")
    url = f"{ADMIN_BASE_URL}/prompts/"
    headers = get_auth_headers()

    # Create
    print("\n--- Testing Create Prompt ---")
    prompt_data = {"name": "My Test Prompt", "type": "positive", "content": "masterpiece"}
    response = requests.post(url, json=prompt_data, headers=headers)
    print_response(response)
    assert response.status_code == 200
    prompt_id = response.json()["id"]

    # Read
    print("\n--- Testing Read Prompts ---")
    response = requests.get(url, headers=headers)
    print_response(response)
    assert response.status_code == 200
    assert any(p["id"] == prompt_id for p in response.json())

if __name__ == "__main__":
    try:
        test_01_register_user()
        test_02_login()
        test_03_read_current_user()
        test_04_admin_endpoints()
        test_05_images_api()
        test_06_inspirations_crud()
        test_07_tasks_api()
        test_08_workflows_crud()
        test_09_prompts_crud()
        
        print_test_header("All Tests Passed!")
        print("The full API test suite completed successfully.")

    except Exception as e:
        print_test_header("Test Failed!")
        print(f"An error occurred during the test run: {e}")
        print("--- Traceback ---")
        traceback.print_exc()
        print("-------------------")