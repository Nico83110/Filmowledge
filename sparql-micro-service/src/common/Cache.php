<?php
namespace frmichel\sparqlms\common;

use Monolog\Logger;
use Exception;

/**
 * Implement the management of the cache database, MongoDB in this case.
 *
 * @author fmichel
 */
class Cache
{

    /**
     * Default cache expiration time in seconds.
     * 2592000s = 30 days
     *
     * @var integer
     */
    const CACHE_EXP_SEC = 2592000;

    /**
     *
     * @var Cache
     */
    private static $singleton = null;

    /**
     *
     * @var \Monolog\Logger
     */
    private $logger = null;

    /**
     * DB connection string with default value
     *
     * @var string
     */
    private $cacheEndpoint = "mongodb://localhost:27017";

    /**
     * DB instance name with default value
     *
     * @var string
     */
    private $cacheDbName = "sparql_micro_service";

    /**
     * MongoDB database collection
     *
     * @var \MongoDB\Collection
     */
    private $cacheDb = null;

    /**
     * Constructor method.
     *
     * @param Context $context
     */
    private function __construct($context)
    {
        $this->logger = $context->getLogger("Cache");
        
        if ($context->hasConfigParam('cache_endpoint'))
            $this->cacheEndpoint = $context->getConfigParam('cache_endpoint');
        
        if ($context->hasConfigParam('cache_db_name'))
            $this->cacheDbName = $context->getConfigParam('cache_db_name');
        
        // Create the database client and default collection: 'cache'
        $client = new \MongoDB\Client($this->cacheEndpoint);
        $this->cacheDb = $client->selectCollection($this->cacheDbName, 'cache');
    }

    /**
     * Create and/or get singleton instance
     *
     * @param Context $context
     * @return Cache
     */
    public static function getInstance($context)
    {
        if (is_null(self::$singleton))
            self::$singleton = new Cache($context);
        
        return self::$singleton;
    }

    /**
     * Write a document (query response) to the cache db along with the query and the date it was obtained.
     *
     * @param string $query
     *            the Web API query. Its hash is used as a key
     * @param string $resp
     *            the Web API query response to store in the cache db
     * @param string $service
     *            the Web API service name
     */
    public function write($query, $resp, $service = null)
    {
        try {
            $now = (new \DateTime('now'));
            $this->cacheDb->insertOne([
                'hash' => hash("sha256", $query),
                'service' => $service,
                'fetch_date' => $now->format('Y-m-d H:i:s'),
                'query' => $query,
                'payload' => $resp
            ]);
        } catch (Exception $e) {
            $this->logger->warning("Cannot write to cache db: " . (string) $e);
        }
    }

    /**
     * Try to get a document from the cache db and return it.
     *
     * If it is found and the expiration date is passed, the document is deleted from the cache db.
     *
     * @param string $query
     *            the Web API query. Its hash is used as a key
     * @return string the cached document if found, null otherwise.
     */
    public function read($query)
    {
        $hash = hash("sha256", $query);
        $found = $this->cacheDb->findOne([
            'hash' => $hash
        ]);
        if ($found != null) {
            
            // Create the date interval corresponding to the cache expiration duration
            $context = Context::getInstance();
            $cacheExpirationInterval = new \DateInterval('PT' . $context->getConfigParam('cache_expires_after', self::CACHE_EXP_SEC) . 'S');
            $cacheExpiresAt = new \DateTime($found['fetch_date']);
            $cacheExpiresAt->add($cacheExpirationInterval);
            
            if ($this->logger->isHandling(Logger::DEBUG))
                $this->logger->debug("Cached document expires at: " . $cacheExpiresAt->format('Y-m-d H:i:s'));
            
            if ($cacheExpiresAt >= (new \DateTime('now'))) {
                // If the expiration date is not passed, the document can be returned as is
                
                // Save the date and time at which the document was fetched (for provenance needs)
                $cacheFetchedAt = new \DateTime($found['fetch_date']);
                $context->setCacheHitDateTime($cacheFetchedAt);
                
                return $found['payload'];
            } else {
                // If the expiration date is passed, remove the document from the cache and return null = no cache hit
                if ($this->logger->isHandling(Logger::INFO))
                    $this->logger->info("Cached document found but has expired, removing it.");
                $this->cacheDb->deleteOne([
                    'hash' => $hash
                ]);
                return null;
            }
        } else
            return null;
    }
}
?>