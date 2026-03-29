from core.supabase import supabase

BUCKET = "documents"

def upload_file(
    user_id: str,
    chatbot_id: str,
    filename: str,
    file_bytes: bytes,
    content_type: str
) -> str:
    '''
    Upload file to Supabase storage and get the public URL

    :param user_id: ID of the user uploading the file
    :param chatbot_id: ID of the chatbot the document belongs to
    :param filename: name of the file
    :param file_bytes: bytes of the file to upload
    :param content_type: MIME type of the file
    :returns: public URL of the uploaded file
    '''
    file_path = build_path(user_id, chatbot_id, filename)
    supabase.storage.from_(BUCKET).upload(
        path=file_path,
        file=file_bytes,
        file_options={"content-type": content_type}
    )

    return supabase.storage.from_(BUCKET).get_public_url(file_path)


def delete_file(user_id: str, chatbot_id: str, filename: str):
    '''
    Delete a single file from Supabase storage

    :param user_id: ID of the user
    :param chatbot_id: ID of the chatbot the document belongs to
    :param filename: name of the file to delete
    '''
    file_path = build_path(user_id, chatbot_id, filename)
    supabase.storage.from_(BUCKET).remove([file_path])


def delete_chatbot_files(user_id: str, chatbot_id: str):
    '''
    Delete all files for a given chatbot from Supabase storage

    :param user_id: ID of the user
    :param chatbot_id: ID of the chatbot whose files should be deleted
    '''
    folder = f"{user_id}/{chatbot_id}/"
    files = supabase.storage.from_(BUCKET).list(folder)

    if not files:
        return
    
    paths = [f"{folder}/{file['name']}" for file in files]
    supabase.storage.from_(BUCKET).remove(paths)
