(async () => {
    const dbs = await indexedDB.databases();
    for (const { name } of dbs) {
        console.log(`导出数据库: ${name}`);
        const req = indexedDB.open(name);
        req.onsuccess = () => {
            const db = req.result;
            const exportData = {};
            const tx = db.transaction(db.objectStoreNames, "readonly");

            let pending = db.objectStoreNames.length;
            for (const storeName of db.objectStoreNames) {
                const store = tx.objectStore(storeName);
                const allReq = store.getAll();
                allReq.onsuccess = () => {
                    exportData[storeName] = allReq.result;
                    if (--pending === 0) {
                        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
                        const a = document.createElement("a");
                        a.href = URL.createObjectURL(blob);
                        a.download = `${name}.json`;
                        a.click();
                    }
                };
            }
        };
    }
})();