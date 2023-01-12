use crate::serenity;
use crate::Arc;
use crate::Context;
use crate::Error;
use crate::Level;
use bytecheck::CheckBytes;
use rkyv::de::deserializers::SharedDeserializeMap;
use rkyv::validation::validators::DefaultValidator;
use rkyv::{Archive, Deserialize, Serialize};
use rocksdb::SliceTransform;
use rocksdb::DB;

#[derive(Clone)]
pub struct Db {
    pub db: Arc<rocksdb::DB>,
    pub cache: rocksdb::Cache,
}

#[derive(Debug)]
pub enum DBFailure {
    Error(rocksdb::Error),
    // CfError,
    SerError,
}

fn extractor_fn(key: &[u8]) -> &[u8] {
    // let mut keyarr = [0u8; 16];
    // keyarr.copy_from_slice(&key);
    // &(u128::from_le_bytes(keyarr) >> 64).to_le_bytes()
    &key[..8]
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
            let prefix_extractor = SliceTransform::create("guildid extractor", extractor_fn, None);
            opts.set_prefix_extractor(prefix_extractor);
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
        let Ok(entry) = (unsafe {rkyv::from_bytes_unchecked::<Level>(&value)}) else {
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

pub fn ids_to_bytes(gid: u64, uid: u64) -> Vec<u8> {
    // ((gid as u128) << 64 | uid as u128).to_le_bytes()
    let mut id = gid.to_le_bytes().to_vec();
    id.append(&mut uid.to_le_bytes().to_vec());
    id
}
