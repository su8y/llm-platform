# Docker Hub의 minio/minio 저장소가 삭제되어 Milvus 팀이 유지하는 미러를 사용한다.
# https://github.com/milvus-io/milvus/pull/53891
FROM milvusdb/minio:RELEASE.2024-12-18T13-15-44Z
CMD ["minio", "server", "/minio_data", "--console-address", ":9001"]
