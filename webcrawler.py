import requests
from bs4 import BeautifulSoup
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures
import time
import os
import socket
import multiprocessing
import urllib.request
from ip2geotools.databases.noncommercial import DbIpCity

#file_lock = Lock()

keyword = ['phishing',
'government agency scam',
'online shopping fraud',
'recruitment scam',
'sextortion',
'lottery scam',
'banking scam',
'malware scam',
'advance fee scam',
'ponzi scheme']

def crawl(url, file_path, file_lock, is_last_level):
    try:
        # pid = os.getpid()
        # print(f"Executing our Task on Process {pid}")
        # response = requests.get()
        wordcount = []
        response = requests.get(url, timeout=5)
        response_time = response.elapsed.total_seconds()
        ip = socket.gethostbyname(response.url.split('//')[1].split('/')[0])
        region = DbIpCity.get(ip, api_key='free').region
        # ip = response.raw._fp.fp.raw._sock.getpeername()
        # ip = socket.gethostbyname(url)
        soup = BeautifulSoup(response.content, "html.parser")
        page_content = urllib.request.urlopen(url).read().decode('utf-8')
        for word in keyword:
            position = page_content.find(word)
            if position == -1:
                wordcount.append('0')
            else:
                wordcount.append('1')
        links = []
        if not is_last_level:
            links = [a["href"] for a in soup.find_all(
                "a", href=True) if a["href"].startswith("http")]

            links = list(set(links))

        # Filter out already visited URLs
        # links = [link for link in links if link not in visited_urls]

        # Filter out duplicates and already visited URLs
        new_links = []
        # Add new links to the text file with file lock
        with file_lock:

            with open(file_path, "r") as file:
                existing_links = file.readlines()
                for link in links:
                    if link + "\n" not in existing_links:
                        new_links.append(link)
            #print(updated_existing_links)
            with open("visited.txt", "a") as file:
                line = url + "," + ip + "," + region + "," + str(response_time)
                for count in wordcount:
                    line = line + "," + count
                line = line.replace("\n","")
                print(line)
                file.write(line + "\n")


            # Add new links to the text file
            with open(file_path, "a") as file:
                for link in new_links:
                    file.write(link + "\n")

        return new_links


        # ip = response.json()  # Extract the IP address from the response

        # Add new links to the text file
        #with file_lock:
        # with open("links.txt", "a") as file:
        #     for link in links:
        #         file.write(link + "\n")

        # return links
    except Exception as e:
        print(f"Error crawling {url}: {e}")
        return []

# Main function to manage crawling using parallel processes


def main(start_url, num_workers=5, max_depth=2):
    print("Crawling started.")
    start_time = time.time()
    visited_urls = set()
    visited_urls.add(start_url)
    file_path = "links.txt"

    # Create a multiprocessing manager to create a shared lock
    manager = multiprocessing.Manager()
    file_lock = manager.Lock()

    with open("links.txt", "w") as file:
        file.write(start_url + "\n")
    with open("visited.txt", "w") as file:
        title = "URL,IP,Region,Response_time"
        for word in keyword:
            title = title + "," + word
        file.write(title + "\n")

    pointer = 0

    depth = 1
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        while depth <= max_depth:

            print(f"Processing depth {depth}...")
            start_time = time.time()
            next_pointer = len(open(file_path).readlines())
            futures = [executor.submit(crawl, url, file_path, file_lock, depth==max_depth) for url in open(file_path).readlines()[pointer:]]
            pointer = next_pointer

            for future in concurrent.futures.as_completed(futures):
                links = future.result()

            
            depth += 1
            print(
                f"Depth {depth} processed in {time.time() - start_time:.2f} seconds.")
    print("Crawling completed.")
    print(f"Crawling completed in {time.time() - start_time:.2f} seconds.")


# Example usage
if __name__ == "__main__":
    # Replace this with your desired starting URL
    start_url = "https://en.wikipedia.org/wiki/Lottery_scam"
    main(start_url, num_workers=5, max_depth=2)
