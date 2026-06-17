CREATE POLICY "Allow public upload to court_images"
ON storage.objects FOR INSERT
WITH CHECK (bucket_id = 'court_images');

CREATE POLICY "Allow public select from court_images"
ON storage.objects FOR SELECT
USING (bucket_id = 'court_images');

CREATE POLICY "Allow public update on court_images"
ON storage.objects FOR UPDATE
USING (bucket_id = 'court_images');

CREATE POLICY "Allow public delete on court_images"
ON storage.objects FOR DELETE
USING (bucket_id = 'court_images');