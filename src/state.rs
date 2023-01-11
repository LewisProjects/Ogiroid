use crate::serenity;
use crate::Arc;
use crate::Context;
use crate::Error;
use crate::Level;
use bytecheck::CheckBytes;
use rkyv::de::deserializers::SharedDeserializeMap;
use rkyv::validation::validators::DefaultValidator;
use rkyv::{Archive, Deserialize, Serialize};
use rocksdb::DB;

#[derive(Clone)]
pub struct Db {
    pub db: Arc<rocksdb::DB>,
    pub cache: rocksdb::Cache,
}

#[derive(Debug)]
pub enum DBFailure {
    Error(rocksdb::Error),
    CfError,
    SerError,
}

impl Db {
    pub fn new(path: &str, cache_capacity: usize) -> Result<Self, Box<dyn std::error::Error>> {
        let cache = rocksdb::Cache::new_lru_cache(128)?;
        let db = {
            let mut opts = rocksdb::Options::default();
            opts.set_compression_type(rocksdb::DBCompressionType::Lz4);
            opts.create_missing_column_families(true);
            opts.set_row_cache(&cache);
            opts.create_if_missing(true);
            opts.set_max_background_jobs(4);
            Arc::new(DB::open_cf_descriptors(&opts, path, vec![])?)
        };
        Ok(Db { db, cache })
    }
}

impl Db {
    pub fn get_bytes<'a, K>(&'a self, key: K) -> Option<Vec<u8>>
    where
        K: AsRef<[u8]>,
    {
        let Ok(Some(value)) = self.db.get(key) else {
            return None};
        Some(value)
    }
    pub fn get<'a, K>(&'a self, key: K) -> Option<Level>
    where
        K: AsRef<[u8]>,
    {
        let Ok(Some(value)) = self.db.get(key) else {
            return None
        };
        let Ok(entry) = (rkyv::from_bytes::<Level>(&value)) else {
            return None
        };
        Some(entry)
    }
    pub fn put<'a, K>(&'a self, key: K, value: Level) -> Result<(), DBFailure>
    where
        K: AsRef<[u8]>,
    {
        let Ok(value) = rkyv::to_bytes::<_, 256>(&value) else {
            return Err(DBFailure::SerError)};
        match self.db.put(key, value) {
            Err(error) => Err(DBFailure::Error(error)),
            Ok(_) => Ok(()),
        }
    }
}

pub fn ids_to_bytes(gid: u64, uid: u64) -> [u8; 16] {
    ((gid as u128) << 64 | uid as u128).to_le_bytes()
}
