use crate::serenity;
use crate::Arc;
use crate::Context;
use crate::Error;
use crate::Level;
use bytecheck::CheckBytes;
use rkyv::de::deserializers::SharedDeserializeMap;
use rkyv::validation::validators::DefaultValidator;
use rkyv::{Archive, Deserialize, Serialize};
use rocksdb::ColumnFamilyDescriptor;
use rocksdb::Options;
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
    pub fn new(
        path: &str,
        cache_capacity: usize,
        cf_names: &[String],
    ) -> Result<Self, Box<dyn std::error::Error>> {
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
            Arc::new(DB::open_cf_descriptors(
                &opts,
                path,
                cf_names
                    .into_iter()
                    .map(|x| ColumnFamilyDescriptor::new(x, Options::default())),
            )?)
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
    pub fn get_bytes_cf<'a, K>(&'a self, key: K, cf: &str) -> Option<Vec<u8>>
    where
        K: AsRef<[u8]>,
    {
        let Some(cf) = self.db.cf_handle(cf) else {
            return None
        };
        let Ok(Some(value)) = self.db.get_cf(&cf, key) else {
            return None};
        Some(value)
    }
    pub fn get<'a, K, T>(&'a self, key: K) -> Option<T>
    where
        T: rkyv::Archive,
        <T as Archive>::Archived: Deserialize<T, SharedDeserializeMap>,
        K: AsRef<[u8]>,
    {
        let Ok(Some(value)) = self.db.get(key) else {
            return None
        };
        let Ok(entry) = (unsafe {rkyv::from_bytes_unchecked::<T>(&value)}) else {
            return None
        };
        Some(entry)
    }
    pub fn get_cf<'a, K, T>(&'a self, key: K, cf: &str) -> Option<T>
    where
        T: rkyv::Archive,
        <T as Archive>::Archived: Deserialize<T, SharedDeserializeMap>,
        K: AsRef<[u8]>,
    {
        let Some(cf) = self.db.cf_handle(cf) else {
            return None
        };
        let Ok(Some(value)) = self.db.get_cf(&cf, key) else {
            return None
        };
        let Ok(entry) = (unsafe {rkyv::from_bytes_unchecked::<T>(&value)}) else {
            return None
        };
        Some(entry)
    }
    pub fn put<'a, K, T>(&'a self, key: K, value: T) -> Result<(), DBFailure>
    where
        T: rkyv::Serialize<
            rkyv::ser::serializers::CompositeSerializer<
                rkyv::ser::serializers::AlignedSerializer<rkyv::AlignedVec>,
                rkyv::ser::serializers::FallbackScratch<
                    rkyv::ser::serializers::HeapScratch<256>,
                    rkyv::ser::serializers::AllocScratch,
                >,
                rkyv::ser::serializers::SharedSerializeMap,
            >,
        >,
        K: AsRef<[u8]>,
    {
        let Ok(value) = rkyv::to_bytes::<_, 256>(&value) else {
            return Err(DBFailure::SerError)};
        match self.db.put(key, value) {
            Err(error) => Err(DBFailure::Error(error)),
            Ok(_) => Ok(()),
        }
    }
    pub fn put_cf<'a, K, T>(&'a self, key: K, value: T, cf: &str) -> Result<(), DBFailure>
    where
        T: rkyv::Serialize<
            rkyv::ser::serializers::CompositeSerializer<
                rkyv::ser::serializers::AlignedSerializer<rkyv::AlignedVec>,
                rkyv::ser::serializers::FallbackScratch<
                    rkyv::ser::serializers::HeapScratch<512>,
                    rkyv::ser::serializers::AllocScratch,
                >,
                rkyv::ser::serializers::SharedSerializeMap,
            >,
        >,
        K: AsRef<[u8]>,
    {
        let cf = self.db.cf_handle(cf).ok_or(DBFailure::SerError)?;
        let Ok(value) = rkyv::to_bytes::<_, 512>(&value) else {
            return Err(DBFailure::SerError)};
        match self.db.put_cf(&cf, key, value) {
            Err(error) => Err(DBFailure::Error(error)),
            Ok(_) => Ok(()),
        }
    }
    pub fn guild_records<'a>(
        &'a self,
        guild_id: u64,
        cf: &str,
    ) -> Option<impl Iterator<Item = (u64, Level)> + 'a> {
        let Some(cf) = self.db.cf_handle(cf) else {
            return None
        };
        Some(self.db
            .prefix_iterator_cf(&cf, guild_id.to_le_bytes())
            .filter_map(|x| {
                if let Ok((key, value)) = x {
                    let Ok(entry) = (unsafe {rkyv::from_bytes_unchecked::<Level>(&value)}) else {
            return None
        };
                    let mut keyarr = [0u8; 8];
                    keyarr.copy_from_slice(&key[8..16]);
                    Some((u64::from_le_bytes(keyarr), entry))
                } else {
                    None
                }
            }))
    }
}

pub fn ids_to_bytes(gid: u64, uid: u64) -> Vec<u8> {
    // ((gid as u128) << 64 | uid as u128).to_le_bytes()
    let mut id = gid.to_le_bytes().to_vec();
    id.extend_from_slice(&uid.to_le_bytes());
    id
}
