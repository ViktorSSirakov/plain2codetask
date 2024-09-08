import argparse
import requests
import os
import logging
import shutil
import subprocess

logging.basicConfig(level=logging.WARN, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
def load_existing_files(build_folder):
    """Load all existing files in The Build Folder. It is from github"""
    existing_files = {}
    try:
        for root, _, files in os.walk(build_folder):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, build_folder)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    existing_files[relative_path] = content
                except Exception as e:
                    logger.warning(f"Failed to read file {file_path}: {str(e)}")
        
        return existing_files
    except Exception as e:
        logger.error(f"Failed to load existing files: {str(e)}")
        return {}
    
def does_plain_file_exist(filename):
    try:
        open(file = filename, mode = 'r')
        return True
    except FileNotFoundError:
        logger.error('No such file')
        return False
def clear_folder(address):
    for item in os.listdir(address):
        item = address + f'\\{item}'
        if os.path.isdir(item):
            shutil.rmtree(item)
        else:
            os.unlink(item)

def copy_base_files(base_folder, build_folder, verbose):
    try:
        if os.path.exists(base_folder):
            for item in os.listdir(base_folder):
                src = os.path.join(base_folder, item)
                dst = os.path.join(build_folder, item)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                elif os.path.isdir(src):
                    shutil.copytree(src, dst)
                if verbose:
                    print(f'The files were copied to {build_folder}')    
        else:
            logger.error('No such folder!')
    except Exception as e:
        logger.error(f"Failed to copy files from base folder: {str(e)}")

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('plain_file')
    parser.add_argument('-v', '--verbose', action='store_true', required = False, help = 'Get extra messeges!')
    parser.add_argument('-b', '--build-folder', type = str, default = 'build', help = 'Build folder location')
    parser.add_argument('-c', '--copy-base-folder', type=str, action = 'store', help = 'Copy the base folder.')
    parser.add_argument('-t', '--test-code', action='store_true')
    args = parser.parse_args()
    
    plain_source_file = args.plain_file
    if does_plain_file_exist(plain_source_file):
        verbose = args.verbose
        if verbose:
            print('Verbose mode is activated!')
        build_folder = os.path.abspath( args.build_folder)
        if os.path.exists(build_folder) and os.path.isdir(build_folder):
            contents = os.listdir(build_folder)
            if contents != []:
                clear_folder(build_folder)
            if verbose:
                print('The folder is ready!')
        else:
            if verbose:
                print(f"The folder '{build_folder}' will be created.")
            os.makedirs(build_folder)
        if type(args.copy_base_folder) == str:
            copy_base_files(build_folder, args.copy_base_folder, verbose)
        base_url = "https://api.codeplain.ai"
        api_url_plain_sections = base_url + "/plain_sections"
        headers_plain_sections = {
            "X-API-Key": os.environ.get('CLAUDE_API_KEY'),
            "Content-Type": "application/json"
        }
        with open(plain_source_file , 'r') as file:
            plain_source_content = file.read()
        payload_plain_sections = {
            "plain_source": plain_source_content
        }
        
        response_plain_sections = requests.post(api_url_plain_sections, headers = headers_plain_sections, json = payload_plain_sections)
        if verbose:
            print(f'The code will do {response_plain_sections.json()} \n\n\n')
        file_data = response_plain_sections.json()
        print(f'Rendering {plain_source_file} to software code: \n')
        do_unit_test = args.test_code
        for i in range(1, len(file_data['Functional Requirements:']) + 1):
            print(f'Rendering the {i} functional requierment:')
            print(file_data['Functional Requirements:'][i - 1])
            api_url_render_functional_requierments = base_url + "/render_functional_requirement"
            headers_rendering = {
                "X-API-Key": "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",
                "Content-Type": "application/json"
            }
            payload_rendering = {
                "frid": i,
                "plain_sections": file_data,
                "existing_files_content": load_existing_files(build_folder)
            }
            response_rendering = requests.post(api_url_render_functional_requierments, headers=headers_rendering, json=payload_rendering)
            for title, code in response_rendering.json().items():
                
                file_path = os.path.join(build_folder, title)
                with open(file_path, 'w') as file:
                    file.write(code)
            if do_unit_test:
                api_url_fix = base_url + "/fix_unittest_issues"
                try:
                    subprocess.run('run_unittest.bat', shell = True, capture_output=True, text=True)
                    test_passed = True
                except subprocess.CalledProcessError:
                    test_passed = False
                if not test_passed:
                    fix_attempts = 0
                    while not test_passed and fix_attempts < 5:
                        if verbose:
                            print(f'This is the {fix_attempts} attempt to fix!')
                        fix_result = requests.post(api_url_fix, file_data, load_existing_files(build_folder), i, build_folder)
                        for title, code in fix_result.json().items():
                            
                            file_path = os.path.join(build_folder, title)
                            with open(file_path, 'w') as file:
                                file.write(code)
                        if do_unit_test:
                            api_url_fix = base_url + "/fix_unittest_issues"
                            try:
                                subprocess.run('run_unittest.bat', shell = True, capture_output=True, text=True)
                                test_passed = True
                            except subprocess.CalledProcessError:
                                test_passed = False
                        fix_attempts += 1
if __name__ == '__main__':
    main()






































