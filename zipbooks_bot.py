import requests

# Set up headers and payload
headers = {
    'Content-Type': 'application/json',
}

json_data = {
    'email': 'mrpickaboo23@gmail.com',
    'password': 'Neverchange0',
}

try:
    # Send the POST request to the ZipBooks API
    response = requests.post('https://api.zipbooks.com/v2/auth/login', headers=headers, json=json_data, timeout=10)

    # Check if the request was redirected
    if response.history:
        print("Request was redirected")
        for resp in response.history:
            print(resp.status_code, resp.url)
    else:
        print("Request was not redirected")

    # Print the status code of the response
    print("Status Code:", response.status_code)

    # Print the content of the response
    print("Response Text:", response.text)

except requests.exceptions.RequestException as e:
    # Print the error message if the request fails
    print(f"Request failed: {e}")
